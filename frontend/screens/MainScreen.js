import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { signOut } from 'firebase/auth';
import { collection, addDoc } from 'firebase/firestore';
import Constants from 'expo-constants';
import { auth, db } from '../config/firebase';

// Use same host as Expo dev server so physical devices can reach your backend
const getBackendUrl = () => {
  const hostUri = Constants.expoConfig?.hostUri ?? Constants.manifest?.debuggerHost;
  const host = hostUri ? hostUri.split(':')[0] : 'localhost';
  return `http://${host}:3000`;
};
const BACKEND_URL = getBackendUrl();

export default function MainScreen({ navigation }) {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const pickerInProgress = useRef(false);

  const pickImage = async () => {
    if (pickerInProgress.current) return;
    setError(null);
    pickerInProgress.current = true;
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (permission.status !== 'granted') {
        Alert.alert('Permission Required', 'Permission to access gallery is required.');
        return;
      }
      // Short delay so native picker can clean up after a previous open (fixes second-tap not opening)
      await new Promise((r) => setTimeout(r, 100));
      const pickerResult = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });
      if (!pickerResult.canceled) {
        setImage(pickerResult.assets[0]);
        setResult(null);
      }
    } catch (err) {
      console.error('Gallery error:', err);
      const message = err?.message || String(err);
      setError(message);
      Alert.alert('Gallery Error', message);
    } finally {
      pickerInProgress.current = false;
    }
  };

  const cameraInProgress = useRef(false);

  const takePhoto = async () => {
    if (cameraInProgress.current) return;
    setError(null);
    cameraInProgress.current = true;
    try {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (permission.status !== 'granted') {
        Alert.alert('Permission Required', 'Camera permission is required.');
        return;
      }
      await new Promise((r) => setTimeout(r, 100));
      const cameraResult = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });
      if (!cameraResult.canceled) {
        setImage(cameraResult.assets[0]);
        setResult(null);
      }
    } finally {
      cameraInProgress.current = false;
    }
  };

  const uploadAndPredict = async () => {
    if (!image) {
      Alert.alert('No Image', 'Please select or capture an image first.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      
      if (Platform.OS === 'web') {
        const response = await fetch(image.uri);
        const blob = await response.blob();
        formData.append('file', blob, 'wound.jpg');
      } else {
        formData.append('file', {
          uri: image.uri,
          name: 'wound.jpg',
          type: 'image/jpeg',
        });
      }
      
      const res = await fetch(`${BACKEND_URL}/image/predict`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const txt = await res.text();
        let message = `Request failed (${res.status})`;
        try {
          const errData = JSON.parse(txt);
          message = errData.error || errData.detail || message;
        } catch (_) {}
        throw new Error(message);
      }
      const data = await res.json();
      setResult(data);
      if (auth.currentUser) {
        try {
          await addDoc(collection(db, 'predictions'), {
            userId: auth.currentUser.uid,
            imageUri: image.uri,
            riskLevel: data.riskLevel,
            probabilities: data.probabilities,
            timestamp: new Date().toISOString(),
          });
        } catch (firestoreError) {
          console.error('Error saving prediction to Firestore:', firestoreError);
        }
      }
    } catch (err) {
      setError(err.message);
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      navigation.replace('Login');
    } catch (error) {
      Alert.alert('Error', 'Failed to logout. Please try again.');
    }
  };

  const clearImage = () => {
    setImage(null);
    setResult(null);
    setError(null);
    setLoading(false);
  };

  const getRiskColor = (riskLevel) => {
    if (riskLevel === 'Low' || riskLevel === 'Healthy') return '#4CAF50';
    if (riskLevel === 'Medium' || riskLevel === 'Moderate') return '#FF9800';
    return '#F44336';
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Wound Infection</Text>
            <Text style={styles.subtitle}>Detection System</Text>
          </View>
          <TouchableOpacity
            style={styles.logoutButton}
            onPress={handleLogout}
          >
            <Ionicons name="log-out-outline" size={24} color="#666" />
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Upload Wound Image</Text>
          <Text style={styles.cardDescription}>
            Capture or select an image to analyze for infection risk
          </Text>

          {image && image.uri ? (
            <View style={styles.imageContainer}>
              <Image 
                source={{ uri: String(image.uri) }} 
                style={styles.preview}
                resizeMode="cover"
              />
              <TouchableOpacity
                style={styles.removeButton}
                onPress={clearImage}
                activeOpacity={0.7}
              >
                <Ionicons name="close-circle" size={32} color="#F44336" />
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.placeholderContainer}>
              <Ionicons name="camera-outline" size={64} color="#ccc" />
              <Text style={styles.placeholderText}>No image selected</Text>
            </View>
          )}

          <View style={styles.buttonRow}>
            <TouchableOpacity
              style={[styles.actionButton, styles.secondaryButton, { marginRight: 6 }]}
              onPress={pickImage}
              disabled={!!loading}
            >
              <Ionicons name="images-outline" size={20} color="#4A90E2" />
              <Text style={[styles.secondaryButtonText, { marginLeft: 8 }]}>Gallery</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.actionButton, styles.secondaryButton, { marginLeft: 6 }]}
              onPress={takePhoto}
              disabled={!!loading}
            >
              <Ionicons name="camera-outline" size={20} color="#4A90E2" />
              <Text style={[styles.secondaryButtonText, { marginLeft: 8 }]}>Camera</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[
              styles.primaryButton,
              (!image || loading) ? styles.disabledButton : null,
            ]}
            onPress={uploadAndPredict}
            disabled={!image || !!loading}
          >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <>
                  <Ionicons name="analytics-outline" size={20} color="#fff" />
                  <Text style={[styles.primaryButtonText, { marginLeft: 8 }]}>Analyze Image</Text>
                </>
              )}
          </TouchableOpacity>
        </View>

        {result && (
          <View style={styles.resultCard}>
            <View style={styles.resultHeader}>
              <Ionicons name="checkmark-circle" size={32} color={getRiskColor(result.riskLevel)} />
              <Text style={[styles.resultTitle, { marginLeft: 12 }]}>Analysis Result</Text>
            </View>

            <View style={[styles.riskBadge, { backgroundColor: `${getRiskColor(result.riskLevel)}20` }]}>
              <Text style={[styles.riskLevel, { color: getRiskColor(result.riskLevel) }]}>
                {result.riskLevel === 'healthy' ? 'Healthy' : 'Infected'}
              </Text>
            </View>

            {result.probabilities && (
              <View style={styles.probabilityContainer}>
                <View style={[styles.probabilityRow, { marginBottom: 12 }]}>
                  <View style={styles.probabilityLabel}>
                    <Ionicons name="checkmark-circle" size={20} color="#4CAF50" />
                    <Text style={[styles.probabilityText, { marginLeft: 8 }]}>Healthy</Text>
                  </View>
                  <Text style={[styles.probabilityValue, { color: '#4CAF50' }]}>
                    {(result.probabilities.healthy * 100).toFixed(1)}%
                  </Text>
                </View>
                <View style={styles.probabilityRow}>
                  <View style={styles.probabilityLabel}>
                    <Ionicons name="warning" size={20} color="#F44336" />
                    <Text style={[styles.probabilityText, { marginLeft: 8 }]}>Infected</Text>
                  </View>
                  <Text style={[styles.probabilityValue, { color: '#F44336' }]}>
                    {(result.probabilities.infected * 100).toFixed(1)}%
                  </Text>
                </View>
              </View>
            )}

            {result.quality && result.quality.issues && result.quality.issues.length > 0 && (
              <View style={styles.qualityWarning}>
                <Ionicons name="information-circle-outline" size={20} color="#FF9800" />
                <Text style={styles.qualityWarningTitle}>Image quality note</Text>
                {result.quality.issues.map((issue, i) => (
                  <Text key={i} style={styles.qualityWarningText}>• {issue}</Text>
                ))}
              </View>
            )}
          </View>
        )}

        {error && (
          <View style={styles.errorCard}>
            <Ionicons name="alert-circle" size={24} color="#F44336" />
            <Text style={[styles.errorText, { marginLeft: 12 }]}>{error}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#E8F4F8',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
    paddingTop: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginTop: 4,
  },
  logoutButton: {
    padding: 8,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    marginBottom: 20,
    shadowColor: '#4A90E2',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 6,
    borderWidth: 1,
    borderColor: '#E0F2F7',
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  cardDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 24,
    lineHeight: 20,
  },
  imageContainer: {
    position: 'relative',
    marginBottom: 20,
    alignItems: 'center',
  },
  preview: {
    width: '100%',
    height: 300,
    borderRadius: 16,
    backgroundColor: '#f0f0f0',
  },
  removeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#fff',
    borderRadius: 16,
  },
  placeholderContainer: {
    height: 200,
    backgroundColor: '#F0F8FB',
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    borderWidth: 2,
    borderColor: '#B8E0F0',
    borderStyle: 'dashed',
  },
  placeholderText: {
    marginTop: 12,
    fontSize: 14,
    color: '#999',
  },
  buttonRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
  },
  secondaryButton: {
    backgroundColor: '#f0f4ff',
    borderWidth: 1,
    borderColor: '#4A90E2',
  },
  secondaryButtonText: {
    color: '#4A90E2',
    fontSize: 16,
    fontWeight: '600',
  },
  primaryButton: {
    backgroundColor: '#4A90E2',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
    borderRadius: 12,
    shadowColor: '#4A90E2',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.5,
  },
  resultCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    marginBottom: 20,
    shadowColor: '#4A90E2',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 6,
    borderWidth: 1,
    borderColor: '#E0F2F7',
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  riskBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 20,
  },
  riskLevel: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  probabilityContainer: {
  },
  probabilityRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  probabilityLabel: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  probabilityText: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  probabilityValue: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  qualityWarning: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#FFF8E1',
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9800',
  },
  qualityWarningTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#E65100',
    marginTop: 4,
    marginBottom: 6,
  },
  qualityWarningText: {
    fontSize: 13,
    color: '#666',
    marginLeft: 4,
    marginBottom: 2,
  },
  errorCard: {
    backgroundColor: '#ffebee',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  errorText: {
    flex: 1,
    color: '#F44336',
    fontSize: 14,
  },
});


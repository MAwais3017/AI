import React, { useState } from 'react';
import {
  ActivityIndicator,
  Image,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';

const BACKEND_URL = 'http://192.168.100.12:3000'; // Your PC's IP address (from server logs)

export default function HomeScreen() {
  const [image, setImage] = useState<any | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'gallery' | 'camera'>('gallery');

  const pickImage = async () => {
    setError(null);
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (permission.status !== 'granted') {
      setError('Permission to access gallery is required.');
      return;
    }
    const pickerResult = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });
    if (!pickerResult.canceled) {
      setImage(pickerResult.assets[0]);
      setResult(null);
    }
  };

  const takePhoto = async () => {
    setError(null);
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (permission.status !== 'granted') {
      setError('Camera permission is required.');
      return;
    }
    const cameraResult = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 0.8,
    });
    if (!cameraResult.canceled) {
      setImage(cameraResult.assets[0]);
      setResult(null);
    }
  };

  const uploadAndPredict = async () => {
    if (!image) {
      setError('Select or capture an image first.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: image.uri,
        name: 'wound.jpg',
        type: 'image/jpeg',
      } as any);
      const res = await fetch(`${BACKEND_URL}/image/predict`, {
        method: 'POST',
        body: formData as any,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Backend error ${res.status}: ${txt}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message ?? 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.badge}>FYP</Text>
          <Text style={styles.title}>Surgical Wound Infection</Text>
          <Text style={styles.subtitle}>AI-based risk assessment from smartphone images.</Text>
        </View>

        {/* Image preview card */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>1. Capture wound image</Text>
          <Text style={styles.sectionSubtitle}>
            Use a clear, well-lit photo taken close to the wound. Avoid heavy shadows or blur.
          </Text>

          <View style={styles.previewContainer}>
            {image ? (
              <View>
                <Image source={{ uri: image.uri }} style={styles.preview} />
                <TouchableOpacity
                  style={styles.clearButton}
                  onPress={() => {
                    setImage(null);
                    setResult(null);
                  }}
                >
                  <Text style={styles.clearButtonText}>✕</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.previewPlaceholder}>
                <Text style={styles.previewPlaceholderText}>No image selected</Text>
                <Text style={styles.previewPlaceholderSub}>Choose Gallery or Camera below</Text>
              </View>
            )}
          </View>

          <View style={styles.toggleRow}>
            <TouchableOpacity
              style={[styles.toggleButton, mode === 'gallery' && styles.toggleButtonActive]}
              onPress={() => setMode('gallery')}
            >
              <Text style={[styles.toggleText, mode === 'gallery' && styles.toggleTextActive]}>
                Gallery
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleButton, mode === 'camera' && styles.toggleButtonActive]}
              onPress={() => setMode('camera')}
            >
              <Text style={[styles.toggleText, mode === 'camera' && styles.toggleTextActive]}>
                Camera
              </Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={styles.primaryButton}
            onPress={mode === 'gallery' ? pickImage : takePhoto}
          >
            <Text style={styles.primaryButtonText}>
              {mode === 'gallery' ? 'Pick from Gallery' : 'Open Camera'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Prediction card */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>2. Run AI infection check</Text>
          <Text style={styles.sectionSubtitle}>
            The model analyses color, texture and wound pattern to estimate infection risk.
          </Text>

          <TouchableOpacity
            style={[styles.primaryButton, !image && styles.primaryButtonDisabled]}
            onPress={uploadAndPredict}
            disabled={loading || !image}
          >
            {loading ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.primaryButtonText}>Predict Risk Level</Text>
            )}
          </TouchableOpacity>

          {error && <Text style={styles.error}>Error: {error}</Text>}

          {result && (
            <View style={styles.resultContainer}>
              <View
                style={[
                  styles.chip,
                  result.riskLevel === 'infected' ? styles.chipDanger : styles.chipSafe,
                ]}
              >
                <Text style={styles.chipText}>
                  {result.riskLevel === 'infected' ? 'HIGH RISK' : 'LIKELY HEALTHY'}
                </Text>
              </View>

              <Text style={styles.resultLabel}>Model output</Text>
              <Text style={styles.resultMainText}>
                Detected risk: <Text style={styles.resultHighlight}>{result.riskLevel}</Text>
              </Text>

              {result.probabilities && (
                <View style={styles.probRow}>
                  <View style={styles.probItem}>
                    <Text style={styles.probLabel}>Healthy</Text>
                    <Text style={styles.probValue}>
                      {(result.probabilities.healthy * 100).toFixed(1)}%
                    </Text>
                  </View>
                  <View style={styles.probItem}>
                    <Text style={styles.probLabel}>Infected</Text>
                    <Text style={styles.probValue}>
                      {(result.probabilities.infected * 100).toFixed(1)}%
                    </Text>
                  </View>
                </View>
              )}

              {result.recommendation && (
                <View style={[
                  styles.recommendationBox,
                  result.riskLevel === 'infected' ? styles.recommendationUrgent : styles.recommendationNormal
                ]}>
                  <Text style={styles.recommendationTitle}>Recommendation:</Text>
                  <Text style={styles.recommendationText}>{result.recommendation}</Text>
                </View>
              )}

              <Text style={styles.disclaimer}>
                This tool is for research and educational use only and does not replace a doctor.
                Always consult a medical professional for diagnosis.
              </Text>
            </View>
          )}
        </View>

        {/* Tips card */}
        <View style={[styles.card, styles.footerCard]}>
          <Text style={styles.sectionTitle}>Best practices for accurate results</Text>
          <Text style={styles.tip}>• Hold the phone 20–30cm from the wound.</Text>
          <Text style={styles.tip}>• Use natural or bright light; avoid strong shadows.</Text>
          <Text style={styles.tip}>• Keep the wound centered and in focus.</Text>
          <Text style={styles.tip}>• Take photos from the same distance every day for tracking.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 16,
  },
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: '#38bdf8',
    color: '#0f172a',
    fontWeight: '600',
    fontSize: 12,
    marginBottom: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#e5e7eb',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#9ca3af',
  },
  card: {
    backgroundColor: '#020617',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1f2937',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e5e7eb',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#9ca3af',
    marginBottom: 12,
  },
  previewContainer: {
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#1f2937',
    backgroundColor: '#020617',
    marginBottom: 12,
  },
  preview: {
    width: '100%',
    aspectRatio: 1,
  },
  previewPlaceholder: {
    paddingVertical: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  previewPlaceholderText: {
    color: '#9ca3af',
    fontWeight: '500',
    marginBottom: 4,
  },
  previewPlaceholderSub: {
    color: '#6b7280',
    fontSize: 12,
  },
  clearButton: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 32,
    height: 32,
    borderRadius: 999,
    backgroundColor: '#ef4444',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#fee2e2',
    zIndex: 20,
  },
  clearButtonText: {
    color: '#f9fafb',
    fontSize: 18,
    fontWeight: '700',
  },
  toggleRow: {
    flexDirection: 'row',
    backgroundColor: '#020617',
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#1f2937',
    padding: 3,
    marginBottom: 10,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  toggleButtonActive: {
    backgroundColor: '#0ea5e9',
  },
  toggleText: {
    fontSize: 13,
    color: '#9ca3af',
    fontWeight: '500',
  },
  toggleTextActive: {
    color: '#0b1120',
    fontWeight: '700',
  },
  primaryButton: {
    marginTop: 4,
    backgroundColor: '#22c55e',
    paddingVertical: 11,
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonDisabled: {
    opacity: 0.5,
  },
  primaryButtonText: {
    color: '#022c22',
    fontWeight: '700',
    fontSize: 14,
  },
  error: {
    marginTop: 8,
    color: '#f97373',
    fontSize: 13,
  },
  resultContainer: {
    marginTop: 12,
  },
  chip: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    marginBottom: 8,
  },
  chipSafe: {
    backgroundColor: '#dcfce7',
  },
  chipDanger: {
    backgroundColor: '#fee2e2',
  },
  chipText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#111827',
  },
  resultLabel: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 2,
  },
  resultMainText: {
    fontSize: 15,
    color: '#e5e7eb',
    marginBottom: 8,
  },
  resultHighlight: {
    fontWeight: '700',
    color: '#22c55e',
    textTransform: 'capitalize',
  },
  probRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  probItem: {
    flex: 1,
  },
  probLabel: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 2,
  },
  probValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#e5e7eb',
  },
  recommendationBox: {
    marginTop: 12,
    marginBottom: 8,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
  },
  recommendationUrgent: {
    backgroundColor: '#fef2f2',
    borderColor: '#fecaca',
  },
  recommendationNormal: {
    backgroundColor: '#f0fdf4',
    borderColor: '#bbf7d0',
  },
  recommendationTitle: {
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 6,
    color: '#111827',
  },
  recommendationText: {
    fontSize: 13,
    lineHeight: 18,
    color: '#374151',
  },
  disclaimer: {
    marginTop: 8,
    fontSize: 11,
    color: '#6b7280',
  },
  footerCard: {
    backgroundColor: '#020617',
  },
  tip: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
  },
});

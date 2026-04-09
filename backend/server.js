const fastify = require('fastify')({ logger: true });
const fetch = require('node-fetch');
const FormData = require('form-data');

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://localhost:8000';


fastify.register(require('@fastify/cors'), {
  origin: '*',
});

fastify.register(require('@fastify/multipart'), {
  limits: {
    fileSize: 10 * 1024 * 1024,
  },
});

fastify.get('/health', async () => {
  return { status: 'ok' };
});

fastify.post('/image/quality-check', async (request, reply) => {
  const contentType = request.headers['content-type'] || request.headers['Content-Type'];
  if (!contentType || !contentType.includes('multipart/form-data')) {
    return reply.code(400).send({ error: 'Request must be multipart/form-data' });
  }
  let file;
  try {
    file = await request.file();
  } catch (err) {
    return reply.code(400).send({ error: 'Failed to parse file', detail: err.message });
  }
  if (!file) {
    return reply.code(400).send({ error: 'Image file is required' });
  }
  const buffer = await file.toBuffer();
  const formData = new FormData();
  formData.append('file', buffer, {
    filename: file.filename || 'image.jpg',
    contentType: file.mimetype || 'image/jpeg',
  });
  try {
    const res = await fetch(`${PYTHON_SERVICE_URL}/quality-check`, {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders(),
    });
    if (!res.ok) {
      const text = await res.text();
      fastify.log.error(`Python quality-check error: ${res.status} ${text}`);
      return reply.code(res.status).send({ error: 'Quality check failed', detail: text });
    }
    const data = await res.json();
    return data;
  } catch (err) {
    fastify.log.error(err);
    return reply.code(500).send({ error: 'Failed to contact Python service' });
  }
});

fastify.post('/image/predict', async (request, reply) => {
  const contentType = request.headers['content-type'] || request.headers['Content-Type'];
  console.log('=== DEBUG: Received Content-Type ===', contentType || 'MISSING/UNDEFINED');
  console.log('=== DEBUG: All headers ===', JSON.stringify(request.headers, null, 2));
  
  if (!contentType || !contentType.includes('multipart/form-data')) {
    return reply.code(400).send({ 
      error: 'Request must be multipart/form-data',
      receivedContentType: contentType || 'none',
      hint: 'In Postman: Body tab → select "form-data" → Key: "file" (type: File) → Select actual image file'
    });
  }
  
  let file;
  try {
    file = await request.file();
  } catch (err) {
    console.log('=== ERROR parsing file ===', err.message);
    return reply.code(400).send({ 
      error: 'Failed to parse file',
      detail: err.message,
      receivedContentType: contentType
    });
  }
  
  if (!file) {
    return reply.code(400).send({ 
      error: 'Image file is required',
      receivedContentType: contentType,
      hint: 'Make sure you are sending form-data with a file field in Postman'
    });
  }

  const buffer = await file.toBuffer();
  const formData = new FormData();
  formData.append('file', buffer, {
    filename: file.filename || 'image.jpg',
    contentType: file.mimetype || 'image/jpeg',
  });

  try {
    const res = await fetch(`${PYTHON_SERVICE_URL}/predict`, {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders(),
    });

    if (!res.ok) {
      const text = await res.text();
      fastify.log.error(`Python service error: ${res.status} ${text}`);
      let message = text;
      try {
        const body = JSON.parse(text);
        message = body.detail || body.error || message;
      } catch (_) {}
      return reply.code(res.status).send({ error: message });
    }

    const data = await res.json();
    return data;
  } catch (err) {
    fastify.log.error(err);
    return reply.code(500).send({ error: 'Failed to contact Python service' });
  }
});

const start = async () => {
  try {
    await fastify.listen({ port: 3000, host: '0.0.0.0' });
    console.log('Server running on http://localhost:3000');
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();

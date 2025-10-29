# Environment Configuration Guide

This directory contains centralized environment configuration management for the Tarot AI Frontend application.

## Overview

The configuration system provides:
- ✅ Centralized environment management
- ✅ Automatic HTTPS enforcement in production
- ✅ Type-safe configuration access
- ✅ Environment-specific settings
- ✅ Configuration validation

## File Structure

```
src/config/
├── env.ts          # Main configuration module
└── README.md       # This file
```

## Usage

### Import Configuration

```typescript
import { config } from '@/config/env';

// Access API URL
console.log(config.apiUrl);

// Access environment
console.log(config.env); // 'development' | 'production' | 'test'

// Access auth provider
console.log(config.authProvider); // 'firebase' | 'jwt'

// Access Firebase config
console.log(config.firebase);

// Access feature flags
console.log(config.features.enableAnalytics);
```

### Environment Variables

Create `.env.local` for development:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Authentication Provider Selection
# Options: 'firebase' | 'jwt'
NEXT_PUBLIC_AUTH_PROVIDER=firebase

# Firebase Configuration (if using Firebase)
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-app.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
```

Create `.env.production` for production:

```bash
# API Configuration (HTTPS enforced automatically)
NEXT_PUBLIC_API_URL=https://your-backend.run.app

# Authentication Provider
NEXT_PUBLIC_AUTH_PROVIDER=firebase

# Firebase Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=your-prod-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-app.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
```

## Environment-Specific Behavior

### Development
- API URL defaults to `http://localhost:8000`
- HTTP connections allowed
- Dev tools enabled
- Analytics disabled

### Production
- API URL defaults to production backend
- HTTP automatically converted to HTTPS
- Dev tools disabled
- Analytics enabled

### Test
- API URL defaults to `http://localhost:8000`
- HTTP connections allowed
- Minimal features enabled

## API Integration

### Using in API Client

```typescript
import { config } from '@/config/env';

const API_BASE_URL = config.apiUrl;

async function fetchData() {
  const response = await fetch(`${API_BASE_URL}/api/v1/data`);
  return response.json();
}
```

### Using in Auth Provider

```typescript
import { config } from '@/config/env';

const API_BASE_URL = config.apiUrl;

async function login(email: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  return response.json();
}
```

## Configuration Options

### `config.env`
Current environment: `'development' | 'production' | 'test'`

### `config.apiUrl`
Backend API URL with automatic HTTPS enforcement in production

### `config.authProvider`
Authentication provider: `'firebase' | 'jwt'`

### `config.firebase`
Firebase configuration object with all required keys

### `config.features`
Feature flags:
- `enableAnalytics`: Enable analytics (production only)
- `enableDevTools`: Enable dev tools (development only)

### `config.api`
API settings:
- `timeout`: Request timeout in milliseconds (default: 30000)
- `retryAttempts`: Number of retry attempts (default: 3)

## Configuration Validation

The configuration is automatically validated when imported in the browser. Errors are logged to the console in development and thrown in production.

Validation checks:
- ✅ API URL is configured
- ✅ Firebase credentials (if Firebase auth is enabled)
- ✅ Required environment variables are set

## Best Practices

1. **Always use the centralized config**
   ```typescript
   // ✅ Good
   import { config } from '@/config/env';
   const apiUrl = config.apiUrl;

   // ❌ Bad
   const apiUrl = process.env.NEXT_PUBLIC_API_URL;
   ```

2. **Don't hardcode URLs**
   ```typescript
   // ✅ Good
   fetch(`${config.apiUrl}/api/v1/users`)

   // ❌ Bad
   fetch('http://localhost:8000/api/v1/users')
   ```

3. **Use environment-specific logic**
   ```typescript
   if (config.env === 'development') {
     console.log('Debug info:', data);
   }
   ```

4. **Check feature flags**
   ```typescript
   if (config.features.enableAnalytics) {
     trackEvent('page_view');
   }
   ```

## Deployment

### Cloud Build

The API URL is automatically configured during build:

```yaml
# cloudbuild.yaml
- name: 'gcr.io/cloud-builders/docker'
  args:
    - 'build'
    - '--build-arg'
    - 'NEXT_PUBLIC_API_URL=https://your-backend.run.app'
```

### Environment Variables in Cloud Run

Set environment variables during deployment:

```bash
gcloud run deploy tarot-frontend \
  --set-env-vars="NEXT_PUBLIC_API_URL=https://your-backend.run.app" \
  --set-env-vars="NEXT_PUBLIC_AUTH_PROVIDER=firebase"
```

## Troubleshooting

### "API URL is not configured"
- Check that `NEXT_PUBLIC_API_URL` is set in your `.env.local`
- Restart the development server after adding environment variables

### "Configuration validation failed"
- Verify all required environment variables are set
- Check the console for specific error messages
- Ensure Firebase credentials are correct (if using Firebase auth)

### HTTPS/HTTP Issues
- In production, HTTP URLs are automatically converted to HTTPS
- Use the config module instead of directly accessing `process.env`
- Clear browser cache if you see mixed content errors

## Migration Guide

If you're migrating from direct environment variable usage:

```typescript
// Before
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// After
import { config } from '@/config/env';
const apiUrl = config.apiUrl;
```

## Additional Resources

- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [Firebase Configuration](https://firebase.google.com/docs/web/setup)
- [Cloud Run Environment Variables](https://cloud.google.com/run/docs/configuring/environment-variables)

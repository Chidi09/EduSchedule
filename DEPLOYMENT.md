# 🚀 EduSchedule Deployment Guide

Complete deployment guide for EduSchedule using **Vercel** (Frontend) and **Railway** (Backend).

## 📋 Prerequisites

- GitHub account
- Vercel account (free tier available)
- Railway account (free tier available)
- Supabase account (free tier available)
- Paystack account (for payments)
- OpenAI API key (for AI features)
- Gemini API key (for AI features)

## 🗄️ Database Setup (Supabase)

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note down your:
   - Project URL: `https://[project-id].supabase.co`
   - Anon (public) Key
   - Service Role Key (keep this secret!)

### Step 2: Create Database Schema

Execute these SQL commands in the Supabase SQL Editor:

```sql
-- Enable RLS
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- Create profiles table linking to auth.users
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'teacher', 'student')),
  school_id UUID REFERENCES schools(id),
  plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'premium')),
  subscription_status TEXT DEFAULT 'inactive' CHECK (subscription_status IN ('active', 'inactive', 'cancelled')),
  deal_offered_at TIMESTAMP,
  deal_expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create schools table
CREATE TABLE schools (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  owner_id UUID REFERENCES auth.users(id) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create teachers table
CREATE TABLE teachers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create rooms table
CREATE TABLE rooms (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  capacity INTEGER DEFAULT 30,
  school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create subjects table
CREATE TABLE subjects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create classes table
CREATE TABLE classes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  grade_level TEXT,
  school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create timetables table
CREATE TABLE timetables (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  term TEXT NOT NULL,
  school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create candidates table (timetable solutions)
CREATE TABLE candidates (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  timetable_id UUID REFERENCES timetables(id) ON DELETE CASCADE,
  metrics JSONB DEFAULT '{}',
  rank INTEGER,
  score INTEGER,
  summary TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create assignments table (individual class assignments)
CREATE TABLE assignments (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
  timetable_id UUID REFERENCES timetables(id) ON DELETE CASCADE,
  teacher_id UUID REFERENCES teachers(id),
  room_id UUID REFERENCES rooms(id),
  subject_id UUID REFERENCES subjects(id),
  class_id UUID REFERENCES classes(id),
  day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
  time_slot INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create security log table for RBAC violations
CREATE TABLE security_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  action TEXT NOT NULL,
  resource TEXT,
  violation_reason TEXT,
  severity TEXT DEFAULT 'medium',
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Row Level Security Policies
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE timetables ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;

-- Policies for profiles
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- Policies for schools
CREATE POLICY "School owners can manage their schools" ON schools
  FOR ALL USING (auth.uid() = owner_id);

CREATE POLICY "School members can view their school" ON schools
  FOR SELECT USING (
    id IN (
      SELECT school_id FROM profiles WHERE id = auth.uid()
    )
  );

-- Policies for teachers (same school access)
CREATE POLICY "Teachers can view same school teachers" ON teachers
  FOR SELECT USING (
    school_id IN (
      SELECT school_id FROM profiles WHERE id = auth.uid()
    )
  );

-- Similar policies for other tables...
-- (Add more policies as needed for your specific requirements)

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schools_updated_at BEFORE UPDATE ON schools
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teachers_updated_at BEFORE UPDATE ON teachers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## 🖥️ Backend Deployment (Railway)

### Step 1: Connect Repository to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `EduSchedule` repository
4. Select the `eduschedule-backend` folder as root directory

### Step 2: Configure Environment Variables

Add these environment variables in Railway Dashboard:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# API Configuration
PYTHON_ENV=production
DEBUG=false

# CORS & Frontend
CORS_ORIGINS=https://your-vercel-app.vercel.app
FRONTEND_URL=https://your-vercel-app.vercel.app

# Payment Configuration
PAYSTACK_PUBLIC_KEY=pk_live_your-live-key
PAYSTACK_SECRET_KEY=sk_live_your-live-key

# AI Services
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key

# JWT Configuration
JWT_SECRET_KEY=your-super-secure-jwt-secret-minimum-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Security
SECRET_KEY=your-super-secret-key-for-production-minimum-32-chars
SECURE_COOKIES=true

# Scheduler Configuration
SCHEDULER_MAX_WORKERS=3
SCHEDULER_TIMEOUT_MINUTES=10
SOLUTION_LIMIT=5

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@yourdomain.com
```

### Step 3: Deploy

Railway will automatically deploy when you push to your main branch.

**Note your Railway app URL**: `https://your-app-name.up.railway.app`

## 🌐 Frontend Deployment (Vercel)

### Step 1: Update Vercel Configuration

Update `eduschedule-frontend/vercel.json` with your Railway URL:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://your-railway-app.up.railway.app/api/$1"
    }
  ]
}
```

### Step 2: Deploy to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project" → Import Git Repository
3. Select your `EduSchedule` repository
4. Set **Root Directory** to `eduschedule-frontend`
5. Framework Preset: **Vite**
6. Build Command: `npm run build`
7. Output Directory: `dist`

### Step 3: Configure Environment Variables

Add these in Vercel Dashboard → Settings → Environment Variables:

```bash
VITE_API_BASE_URL=https://your-railway-app.up.railway.app
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-public-key
VITE_PAYSTACK_PUBLIC_KEY=pk_live_your-live-key
NODE_ENV=production
```

### Step 4: Update Backend CORS

Update your Railway environment variables to include your Vercel URL:

```bash
CORS_ORIGINS=https://your-vercel-app.vercel.app
FRONTEND_URL=https://your-vercel-app.vercel.app
```

## 📱 PWA Assets

Add these icon files to `eduschedule-frontend/public/`:

1. **pwa-192x192.png** (192x192 pixels)
2. **pwa-512x512.png** (512x512 pixels)
3. **apple-touch-icon.png** (180x180 pixels)
4. **favicon-32x32.png** (32x32 pixels)
5. **favicon-16x16.png** (16x16 pixels)

**Quick way to generate icons:**
- Use [favicon.io](https://favicon.io/) or [realfavicongenerator.net](https://realfavicongenerator.net/)
- Upload your logo and download all required sizes

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] All environment variables configured
- [ ] Database schema created in Supabase
- [ ] RLS policies enabled
- [ ] PWA icons generated and added
- [ ] Paystack webhook URL configured

### Post-Deployment Testing
- [ ] Backend API accessible at `/docs`
- [ ] Frontend loads correctly
- [ ] User registration works
- [ ] School creation works
- [ ] Teacher invitation works
- [ ] Timetable generation works
- [ ] PWA install prompt appears on mobile
- [ ] Offline functionality works
- [ ] Payment flow works

### Security Verification
- [ ] RLS policies working (users can't see other schools' data)
- [ ] RBAC working (only admins can create teachers)
- [ ] HTTPS enforced on all endpoints
- [ ] API rate limiting enabled
- [ ] CORS configured correctly

## 🔧 Monitoring & Maintenance

### Railway Monitoring
- Monitor logs in Railway dashboard
- Set up alerts for high memory/CPU usage
- Monitor database connections

### Vercel Monitoring
- Check function invocations and errors
- Monitor Core Web Vitals
- Check deployment logs

### Supabase Monitoring
- Monitor database usage and connections
- Check auth logs for failed attempts
- Monitor API usage

## 🚨 Troubleshooting

### Common Issues

**1. CORS Errors**
```bash
# Fix: Update CORS_ORIGINS in Railway
CORS_ORIGINS=https://your-vercel-app.vercel.app,https://www.your-domain.com
```

**2. Database Connection Issues**
- Verify SUPABASE_URL and keys
- Check RLS policies
- Ensure service role key has proper permissions

**3. PWA Not Installing**
- Verify all icon sizes are present
- Check manifest.json is accessible
- Ensure HTTPS is enabled

**4. Payment Webhooks Failing**
- Configure webhook URL in Paystack dashboard
- Verify webhook signature validation
- Check Railway logs for errors

### Production Optimizations

1. **Enable Redis Caching** (Railway addon)
2. **Set up CDN** for static assets
3. **Enable gzip compression**
4. **Monitor performance** with Sentry
5. **Set up backup strategy** for database

## 📞 Support

- **Railway Issues**: Check Railway dashboard and logs
- **Vercel Issues**: Check Vercel dashboard and function logs
- **Supabase Issues**: Check Supabase dashboard and logs
- **Application Issues**: Check GitHub issues or create new ones

## 🔄 Updates

To deploy updates:

1. **Backend**: Push to main branch → Railway auto-deploys
2. **Frontend**: Push to main branch → Vercel auto-deploys
3. **Database**: Run migrations in Supabase SQL editor

Your EduSchedule application is now production-ready! 🎉
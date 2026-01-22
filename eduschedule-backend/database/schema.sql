-- EduSchedule Database Schema
-- Run this in Supabase SQL Editor to set up your database

-- 1. PROFILES (Extends Supabase Auth)
create table public.profiles (
  id uuid references auth.users not null primary key,
  email text unique not null,
  name text,
  school_name text,
  role text default 'guest',
  plan text default 'free',
  subscription_status text default 'active',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for profiles
alter table public.profiles enable row level security;

create policy "Users can view their own profile"
on public.profiles for select
using ( auth.uid() = id );

create policy "Users can update their own profile"
on public.profiles for update
using ( auth.uid() = id );

-- 2. CORE TABLES

create table public.teachers (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete set null,
  name text not null,
  email text,
  school_id text,
  preferences jsonb default '{}'::jsonb,
  availability jsonb default '{}'::jsonb,
  created_at timestamp with time zone default now()
);

alter table public.teachers enable row level security;

create table public.rooms (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete set null,
  name text not null,
  capacity int not null,
  type text default 'classroom',
  school_id text,
  created_at timestamp with time zone default now()
);

alter table public.rooms enable row level security;

create table public.subjects (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete set null,
  name text not null,
  periods_per_week int default 4,
  is_consecutive boolean default false,
  school_id text,
  created_at timestamp with time zone default now()
);

alter table public.subjects enable row level security;

create table public.classes (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete set null,
  name text not null,
  grade_level int,
  student_count int,
  school_id text,
  created_at timestamp with time zone default now()
);

alter table public.classes enable row level security;

-- 3. TIMETABLE & RESULTS

create table public.timetables (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade,
  term text not null,
  status text default 'draft',
  created_at timestamp with time zone default now()
);

alter table public.timetables enable row level security;

create table public.candidates (
  id text default gen_random_uuid()::text primary key,
  timetable_id uuid references public.timetables(id) on delete cascade,
  metrics jsonb default '{}'::jsonb,
  rank int,
  created_at timestamp with time zone default now()
);

alter table public.candidates enable row level security;

create table public.assignments (
  id uuid default gen_random_uuid() primary key,
  timetable_id uuid references public.timetables(id) on delete cascade,
  candidate_id text references public.candidates(id) on delete cascade,
  class_id uuid references public.classes(id),
  subject_id uuid references public.subjects(id),
  teacher_id uuid references public.teachers(id),
  room_id uuid references public.rooms(id),
  day_of_week int,
  period int,
  created_at timestamp with time zone default now()
);

alter table public.assignments enable row level security;

-- 4. API KEYS (Secure Access)

create table public.api_keys (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade,
  key_hash text not null,
  label text,
  last_used_at timestamp with time zone,
  created_at timestamp with time zone default now()
);

alter table public.api_keys enable row level security;

-- 5. INDEXES for Performance

create index idx_teachers_user_id on public.teachers(user_id);
create index idx_rooms_user_id on public.rooms(user_id);
create index idx_subjects_user_id on public.subjects(user_id);
create index idx_classes_user_id on public.classes(user_id);
create index idx_timetables_user_id on public.timetables(user_id);
create index idx_assignments_timetable_id on public.assignments(timetable_id);
create index idx_assignments_candidate_id on public.assignments(candidate_id);
create index idx_candidates_timetable_id on public.candidates(timetable_id);
create index idx_api_keys_user_id on public.api_keys(user_id);
create index idx_teachers_school_id on public.teachers(school_id);
create index idx_rooms_school_id on public.rooms(school_id);
create index idx_subjects_school_id on public.subjects(school_id);
create index idx_classes_school_id on public.classes(school_id);

-- Run this in your Supabase SQL Editor to initialize your project tables

-- 1. Create the chat_messages table
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    session_id text,
    role text NOT NULL CHECK (role IN ('user', 'assistant')),
    content text NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Turn on Row Level Security (RLS)
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

-- Create policy for user access
CREATE POLICY "Users can only see and create their own messages."
ON public.chat_messages FOR ALL USING (
    auth.uid() = user_id
);


-- 2. Create the mood_history table
CREATE TABLE IF NOT EXISTS public.mood_history (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    emotion text NOT NULL,
    confidence real,
    source text CHECK (source IN ('audio', 'video')),
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Turn on RLS
ALTER TABLE public.mood_history ENABLE ROW LEVEL SECURITY;

-- Create policy for user access
CREATE POLICY "Users can view and insert their own moods."
ON public.mood_history FOR ALL USING (
    auth.uid() = user_id
);

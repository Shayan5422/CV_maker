// src/app/models/resume.model.ts
export interface Resume {
    id?: number;
    title: string;
    full_name: string;
    email: string;
    phone: string;
    summary: string;
    experience: string;
    education: string;
    skills: string;
    updated_at?: string;
    user_id?: number;
}
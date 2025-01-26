// src/app/models/resume.model.ts
export interface Resume {
    id?: number;
    title: string;
    full_name: string;
    email: string;
    phone: string;
    city: string;
    languages: Language[];
    summary: string;
    education: Education[];
    experience: Experience[];
    skills: string[];
    updated_at?: string;
    user_id?: number;
}

export interface Education {
    degree: string;
    school: string;
    field: string;
    startDate: string;
    endDate: string;
}

export interface Experience {
    title: string;
    company: string;
    location: string;
    startDate: string;
    endDate: string;
    description: string;
}

export interface Language {
    name: string;
    proficiency: string;
}
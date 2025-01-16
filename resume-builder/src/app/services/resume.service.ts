// src/app/services/resume.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Resume } from '../models/resume.model';
import { Observable } from 'rxjs';

export interface ResumeTheme {
  id: string;
  name: string;
  colors: {
    primary: string;
    secondary: string;
    background: string;
    text: string;
    accent: string;
  };
  preview: string;
}

@Injectable({
  providedIn: 'root'
})
export class ResumeService {
  private baseUrl = 'http://127.0.0.1:8000';
  private apiUrl = `${this.baseUrl}/resumes`;

  // تم‌های مدرن و جذاب
  readonly themes: ResumeTheme[] = [
    {
      id: 'modern-blue',
      name: 'Modern Blue',
      colors: {
        primary: '#2563eb',
        secondary: '#1d4ed8',
        background: '#f8fafc',
        text: '#1e293b',
        accent: '#60a5fa'
      },
      preview: 'assets/themes/modern-blue.png'
    },
    {
      id: 'elegant-dark',
      name: 'Elegant Dark',
      colors: {
        primary: '#334155',
        secondary: '#1e293b',
        background: '#f1f5f9',
        text: '#0f172a',
        accent: '#94a3b8'
      },
      preview: 'assets/themes/elegant-dark.png'
    },
    {
      id: 'creative-purple',
      name: 'Creative Purple',
      colors: {
        primary: '#7c3aed',
        secondary: '#6d28d9',
        background: '#faf5ff',
        text: '#2e1065',
        accent: '#a78bfa'
      },
      preview: 'assets/themes/creative-purple.png'
    },
    {
      id: 'nature-green',
      name: 'Nature Green',
      colors: {
        primary: '#059669',
        secondary: '#047857',
        background: '#f0fdf4',
        text: '#064e3b',
        accent: '#6ee7b7'
      },
      preview: 'assets/themes/nature-green.png'
    },
    {
      id: 'coral-sunset',
      name: 'Coral Sunset',
      colors: {
        primary: '#f43f5e',
        secondary: '#e11d48',
        background: '#fff1f2',
        text: '#881337',
        accent: '#fda4af'
      },
      preview: 'assets/themes/coral-sunset.png'
    }
  ];

  constructor(private http: HttpClient) {}

  getResumes(): Observable<Resume[]> {
    return this.http.get<Resume[]>(this.apiUrl);
  }

  getResume(id: number): Observable<Resume> {
    return this.http.get<Resume>(`${this.apiUrl}/${id}`);
  }

  createResume(resume: Resume): Observable<Resume> {
    return this.http.post<Resume>(this.apiUrl, resume);
  }

  updateResume(id: number, resume: Resume): Observable<Resume> {
    return this.http.put<Resume>(`${this.apiUrl}/${id}`, resume);
  }

  deleteResume(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.apiUrl}/${id}`);
  }

  downloadResumePDF(id: number, themeId: string): Observable<Blob> {
    const params = new HttpParams().set('theme', themeId);
    return this.http.get(`${this.apiUrl}/${id}/pdf`, {
      params,
      responseType: 'blob',
      headers: {
        'Accept': 'application/pdf'
      }
    });
  }

  getThemes(): ResumeTheme[] {
    return this.themes;
  }
}
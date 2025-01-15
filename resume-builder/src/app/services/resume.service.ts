// src/app/services/resume.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Resume } from '../models/resume.model';
import { AuthService } from './auth.service';

@Injectable({
    providedIn: 'root'
})
export class ResumeService {
    private apiUrl = 'http://127.0.0.1:8000/resumes';

    constructor(
        private http: HttpClient,
        private authService: AuthService
    ) { }

    private getHeaders(): HttpHeaders {
        const token = this.authService.currentUserValue.access_token;
        return new HttpHeaders().set('Authorization', `Bearer ${token}`);
    }

    getResumes(): Observable<Resume[]> {
        return this.http.get<Resume[]>(this.apiUrl, { headers: this.getHeaders() });
    }

    getResume(id: number): Observable<Resume> {
        return this.http.get<Resume>(`${this.apiUrl}/${id}`, { headers: this.getHeaders() });
    }

    createResume(resume: Resume): Observable<Resume> {
        return this.http.post<Resume>(this.apiUrl, resume, { headers: this.getHeaders() });
    }

    updateResume(id: number, resume: Resume): Observable<Resume> {
        return this.http.put<Resume>(`${this.apiUrl}/${id}`, resume, { headers: this.getHeaders() });
    }

    deleteResume(id: number): Observable<any> {
        return this.http.delete(`${this.apiUrl}/${id}`, { headers: this.getHeaders() });
    }
}

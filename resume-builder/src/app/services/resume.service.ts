// src/app/components/services/resume.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Resume } from '../models/resume.model';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ResumeService {
  private apiUrl = 'http://127.0.0.1:8000/resumes';

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
}

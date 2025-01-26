// src/app/components/resume-list/resume-list.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { ResumeService, ResumeTheme } from '../services/resume.service';
import { Resume } from '../models/resume.model';

@Component({
  selector: 'app-resume-list',
  standalone: true,
  imports: [CommonModule, RouterLink, DatePipe],
  templateUrl: './resume-list.component.html',
  styleUrls: ['./resume-list.component.scss']
})
export class ResumeListComponent implements OnInit {
  resumes: Resume[] = [];
  loading = false;
  error = '';
  showThemeModal = false;
  selectedThemeId: string | null = null;
  selectedResume: Resume | null = null;
  themes: ResumeTheme[] = [];

  constructor(
    private resumeService: ResumeService,
    private router: Router
  ) {
    this.themes = this.resumeService.getThemes();
  }

  ngOnInit(): void {
    this.loadResumes();
  }

  get selectedTheme(): ResumeTheme | undefined {
    return this.themes.find(theme => theme.id === this.selectedThemeId);
  }

  loadResumes(): void {
    this.loading = true;
    this.error = '';
    this.resumeService.getResumes().subscribe({
      next: (resumes) => {
        this.resumes = resumes;
        this.loading = false;
      },
      error: (error) => {
        this.error = 'Failed to load resumes. Please try again later.';
        console.error('Error loading resumes:', error);
        this.loading = false;
      }
    });
  }

  createNew(): void {
    this.router.navigate(['/resumes/new']);
  }

  editResume(id: number): void {
    this.router.navigate(['/resumes/edit', id]);
  }

  openThemeModal(resume: Resume): void {
    this.selectedResume = resume;
    this.showThemeModal = true;
  }

  closeThemeModal(): void {
    this.showThemeModal = false;
    this.selectedThemeId = null;
    this.selectedResume = null;
  }

  selectThemeAndDownload(themeId: string): void {
    this.selectedThemeId = themeId;
  }

  downloadWithTheme(): void {
    if (this.selectedThemeId && this.selectedResume?.id) {
      this.resumeService.downloadResumePDF(this.selectedResume.id, this.selectedThemeId).subscribe({
        next: (blob: Blob) => {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `${this.selectedResume?.title.replace(/\s+/g, '_')}_${this.selectedThemeId}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          this.closeThemeModal();
        },
        error: (error) => {
          console.error('Error downloading PDF:', error);
          this.error = 'Failed to download PDF. Please try again.';
          this.closeThemeModal();
        }
      });
    }
  }

  async deleteResume(id?: number): Promise<void> {
    if (id && await this.confirmDelete()) {
      this.loading = true;
      this.resumeService.deleteResume(id).subscribe({
        next: () => {
          this.resumes = this.resumes.filter(resume => resume.id !== id);
          this.loading = false;
        },
        error: (error) => {
          this.error = 'Failed to delete resume. Please try again.';
          console.error('Error deleting resume:', error);
          this.loading = false;
        }
      });
    }
  }

  private confirmDelete(): Promise<boolean> {
    return new Promise(resolve => {
      const result = window.confirm('Are you sure you want to delete this resume?');
      resolve(result);
    });
  }
}
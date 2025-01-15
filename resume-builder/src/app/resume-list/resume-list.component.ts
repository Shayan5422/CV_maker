// src/app/components/resume-list/resume-list.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { ResumeService } from '../services/resume.service';
import { Resume } from '../models/resume.model';

@Component({
  selector: 'app-resume-list',
  standalone: true,
  imports: [CommonModule, RouterLink, DatePipe],
  template: `
    <div class="resume-list-container">
      <div class="header">
        <h2>My Resumes</h2>
        <button class="btn btn-primary" (click)="createNew()">
          <i class="fas fa-plus"></i> Create New Resume
        </button>
      </div>

      @if (error) {
        <div class="alert alert-danger">
          {{ error }}
        </div>
      }

      @if (loading) {
        <div class="loading-spinner">
          <div class="spinner"></div>
          <p>Loading resumes...</p>
        </div>
      }

      @if (!loading && resumes.length === 0) {
        <div class="no-resumes">
          <p>You haven't created any resumes yet.</p>
          <button class="btn btn-primary" (click)="createNew()">
            Create Your First Resume
          </button>
        </div>
      }

      @if (!loading && resumes.length > 0) {
        <div class="resumes-grid">
          @for (resume of resumes; track resume.id) {
            <div class="resume-card">
              <div class="resume-card-header">
                <h3>{{ resume.title }}</h3>
                @if (resume.updated_at) {
                  <div class="badge">
                    Last updated: {{ resume.updated_at | date:'short' }}
                  </div>
                }
              </div>

              <div class="resume-card-content">
                <p><strong>Name:</strong> {{ resume.full_name }}</p>
                <p><strong>Email:</strong> {{ resume.email }}</p>
              </div>

              <div class="resume-card-actions">
                <button class="btn btn-outline" (click)="editResume(resume.id)">
                  <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-outline" (click)="downloadResume(resume)">
                  <i class="fas fa-download"></i> Download PDF
                </button>
                <button class="btn btn-danger" (click)="deleteResume(resume.id)">
                  <i class="fas fa-trash"></i> Delete
                </button>
              </div>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .resume-list-container {
      padding: 2rem;
      background-color: #f5f5f5;
      min-height: 100vh;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;

      h2 {
        margin: 0;
        font-size: 1.8rem;
        color: #2c3e50;
      }
    }

    .alert {
      padding: 1rem;
      border-radius: 4px;
      margin-bottom: 1rem;

      &.alert-danger {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
      }
    }

    .loading-spinner {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem;

      .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      p {
        margin-top: 1rem;
        color: #666;
      }
    }

    .no-resumes {
      text-align: center;
      padding: 3rem;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

      p {
        color: #666;
        margin-bottom: 1.5rem;
      }
    }

    .resumes-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.5rem;
    }

    .resume-card {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      overflow: hidden;
      transition: transform 0.2s ease;

      &:hover {
        transform: translateY(-2px);
      }

      .resume-card-header {
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-bottom: 1px solid #eee;

        h3 {
          margin: 0;
          font-size: 1.2rem;
          color: #2c3e50;
        }

        .badge {
          display: inline-block;
          font-size: 0.8rem;
          color: #666;
          margin-top: 0.5rem;
        }
      }

      .resume-card-content {
        padding: 1.5rem;

        p {
          margin: 0.5rem 0;
          color: #666;

          strong {
            color: #2c3e50;
          }
        }
      }

      .resume-card-actions {
        padding: 1rem 1.5rem;
        background-color: #f8f9fa;
        border-top: 1px solid #eee;
        display: flex;
        gap: 0.5rem;

        button {
          flex: 1;
          font-size: 0.9rem;
        }
      }
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0.5rem 1rem;
      border-radius: 4px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      gap: 0.5rem;
      border: none;

      i {
        font-size: 0.9em;
      }

      &.btn-primary {
        background-color: #3498db;
        color: white;

        &:hover {
          background-color: #2980b9;
        }
      }

      &.btn-outline {
        background-color: white;
        border: 1px solid #ddd;
        color: #666;

        &:hover {
          background-color: #f8f9fa;
          border-color: #aaa;
        }
      }

      &.btn-danger {
        background-color: white;
        border: 1px solid #e74c3c;
        color: #e74c3c;

        &:hover {
          background-color: #e74c3c;
          color: white;
        }
      }
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `]
})
export class ResumeListComponent implements OnInit {
  resumes: Resume[] = [];
  loading = false;
  error = '';

  constructor(
    private resumeService: ResumeService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadResumes();
  }

  loadResumes() {
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

  createNew() {
    this.router.navigate(['/resumes/new']);
  }

  editResume(id?: number) {
    if (id) {
      this.router.navigate(['/resumes/edit', id]);
    }
  }

  async deleteResume(id?: number) {
    if (id && await this.confirmDelete()) {
      this.loading = true;
      this.resumeService.deleteResume(id).subscribe({
        next: () => {
          this.loadResumes();
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

  downloadResume(resume: Resume) {
    // This will be implemented with PDF generation
    console.log('Downloading resume:', resume);
  }
}
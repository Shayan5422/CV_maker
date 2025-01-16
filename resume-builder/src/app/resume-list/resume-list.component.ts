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
    <div class="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
          <div class="flex items-center gap-3">
            <i class="fas fa-file-alt text-2xl text-blue-600"></i>
            <h1 class="text-2xl font-bold text-gray-900">My Resumes</h1>
          </div>
          <button 
            (click)="createNew()"
            class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm">
            <i class="fas fa-plus"></i>
            Create New Resume
          </button>
        </div>

        <!-- Error Alert -->
        @if (error) {
          <div class="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg flex items-center gap-3">
            <i class="fas fa-exclamation-circle text-red-500 text-xl"></i>
            <p class="text-red-700">{{ error }}</p>
          </div>
        }

        <!-- Loading State -->
        @if (loading) {
          <div class="flex flex-col items-center justify-center py-12 space-y-4">
            <div class="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            <p class="text-gray-600">Loading resumes...</p>
          </div>
        }

        <!-- Empty State -->
        @if (!loading && resumes.length === 0) {
          <div class="bg-white rounded-xl shadow-sm p-12 text-center">
            <div class="max-w-sm mx-auto space-y-6">
              <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                <i class="fas fa-file-alt text-2xl text-blue-600"></i>
              </div>
              <div>
                <h3 class="text-lg font-medium text-gray-900">No Resumes Yet</h3>
                <p class="mt-2 text-gray-600">Get started by creating your first resume</p>
              </div>
              <button 
                (click)="createNew()"
                class="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                <i class="fas fa-plus"></i>
                Create Your First Resume
              </button>
            </div>
          </div>
        }

        <!-- Resumes Grid -->
        @if (!loading && resumes.length > 0) {
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            @for (resume of resumes; track resume.id) {
              <div class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-all duration-200 transform hover:-translate-y-1">
                <!-- Card Header -->
                <div class="p-6 bg-gray-50 border-b border-gray-100">
                  <div class="flex justify-between items-start">
                    <h3 class="font-medium text-gray-900 truncate" [title]="resume.title">
                      {{ resume.title }}
                    </h3>
                    @if (resume.updated_at) {
                      <span class="text-xs text-gray-500 flex items-center gap-1">
                        <i class="fas fa-clock"></i>
                        {{ resume.updated_at | date:'short' }}
                      </span>
                    }
                  </div>
                </div>

                <!-- Card Content -->
                <div class="p-6 space-y-3">
                  <div class="flex items-center gap-2 text-gray-600">
                    <i class="fas fa-user text-gray-400"></i>
                    <span>{{ resume.full_name }}</span>
                  </div>
                  <div class="flex items-center gap-2 text-gray-600">
                    <i class="fas fa-envelope text-gray-400"></i>
                    <span>{{ resume.email }}</span>
                  </div>
                </div>

                <!-- Card Actions -->
                <div class="px-6 py-4 bg-gray-50 border-t border-gray-100 flex gap-3">
                  <button 
                    (click)="editResume(resume.id)"
                    class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 text-sm text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                    <i class="fas fa-edit"></i>
                    Edit
                  </button>

                  <button 
                    (click)="downloadResume(resume)"
                    class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 text-sm text-blue-600 bg-white border border-gray-200 rounded-lg hover:bg-blue-50 transition-colors">
                    <i class="fas fa-download"></i>
                    PDF
                  </button>

                  <button 
                    (click)="deleteResume(resume.id)"
                    class="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-600 bg-white border border-gray-200 rounded-lg hover:bg-red-50 transition-colors">
                    <i class="fas fa-trash"></i>
                    Delete
                  </button>
                </div>
              </div>
            }
          </div>
        }
      </div>
    </div>
  `
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
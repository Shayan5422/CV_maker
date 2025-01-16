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

        <!-- Theme Selection Modal -->
        @if (showThemeModal) {
          <div class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <!-- Modal Header -->
              <div class="p-6 border-b border-gray-100">
                <div class="flex justify-between items-center">
                  <h2 class="text-xl font-semibold text-gray-900">Select Resume Theme</h2>
                  <button 
                    (click)="closeThemeModal()"
                    class="text-gray-400 hover:text-gray-500">
                    <i class="fas fa-times text-xl"></i>
                  </button>
                </div>
              </div>
              
              <!-- Theme Grid -->
              <div class="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                @for (theme of themes; track theme.id) {
                  <div 
                    (click)="selectThemeAndDownload(theme.id)"
                    class="group cursor-pointer">
                    <!-- Theme Preview Card -->
                    <div class="relative aspect-[3/4] rounded-lg overflow-hidden border-2 transition-all duration-200"
                         [class.border-blue-500]="selectedThemeId === theme.id"
                         [style.borderColor]="selectedThemeId === theme.id ? theme.colors.primary : ''"
                         [class.shadow-lg]="selectedThemeId === theme.id">
                      <!-- Theme Preview Content -->
                      <div class="absolute inset-0 bg-gradient-to-br"
                           [style.backgroundColor]="theme.colors.background">
                        <!-- Header Area -->
                        <div class="h-1/4" [style.backgroundColor]="theme.colors.primary"></div>
                        <!-- Content Preview -->
                        <div class="p-4">
                          <div class="w-1/2 h-4 rounded" [style.backgroundColor]="theme.colors.secondary"></div>
                          <div class="mt-2 w-3/4 h-3 rounded" [style.backgroundColor]="theme.colors.accent"></div>
                          <div class="mt-4 space-y-2">
                            @for (i of [1,2,3]; track i) {
                              <div class="w-full h-2 rounded" [style.backgroundColor]="theme.colors.text + '20'"></div>
                            }
                          </div>
                        </div>
                      </div>
                      
                      <!-- Hover Overlay -->
                      <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-all duration-200 flex items-center justify-center">
                        <div class="bg-white text-gray-900 px-4 py-2 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transform translate-y-2 group-hover:translate-y-0 transition-all duration-200">
                          Select Theme
                        </div>
                      </div>
                    </div>
                    
                    <!-- Theme Name -->
                    <div class="mt-3 text-center">
                      <h3 class="font-medium text-gray-900">{{ theme.name }}</h3>
                    </div>
                  </div>
                }
              </div>

              <!-- Modal Footer -->
              <div class="p-6 border-t border-gray-100 flex justify-end gap-3">
                <button 
                  (click)="closeThemeModal()"
                  class="px-4 py-2 text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50">
                  Cancel
                </button>
                <button 
                  [disabled]="!selectedThemeId"
                  (click)="downloadWithTheme()"
                  class="px-4 py-2 text-white rounded-lg shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  [style.backgroundColor]="selectedTheme ? selectedTheme.colors.primary : ''"
                  [style.borderColor]="selectedTheme ? selectedTheme.colors.secondary : ''">
                  Download PDF
                </button>
              </div>
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
                    (click)="openThemeModal(resume)"
                    class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 text-sm text-blue-600 bg-white border border-gray-200 rounded-lg hover:bg-blue-50 transition-colors">
                    <i class="fas fa-download"></i>
                    PDF
                  </button>

                  <button 
                    (click)="deleteResume(resume.id)"
                    class="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-600 bg-white border border-gray-200 rounded-lg hover:bg-red-50 transition-colors">
                    <i class="fas fa-trash"></i>
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

  ngOnInit() {
    this.loadResumes();
  }

  get selectedTheme(): ResumeTheme | undefined {
    return this.themes.find(theme => theme.id === this.selectedThemeId);
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

  openThemeModal(resume: Resume) {
    this.selectedResume = resume;
    this.showThemeModal = true;
  }

  closeThemeModal() {
    this.showThemeModal = false;
    this.selectedThemeId = null;
    this.selectedResume = null;
  }

  selectThemeAndDownload(themeId: string) {
    this.selectedThemeId = themeId;
  }

  downloadWithTheme() {
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
}
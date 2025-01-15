// src/app/components/resume-form/resume-form.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ResumeService } from '../services/resume.service';
import { Resume } from '../models/resume.model';

@Component({
  selector: 'app-resume-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="resume-form-container">
      <div class="resume-form-card">
        <h2>{{ isEditing ? 'Edit Resume' : 'Create New Resume' }}</h2>

        <form [formGroup]="resumeForm" (ngSubmit)="onSubmit()">
          <div class="form-group">
            <label for="title">Title</label>
            <input 
              type="text" 
              id="title"
              formControlName="title"
              [class.is-invalid]="submitted && f['title'].errors"
            >
            @if (submitted && f['title'].errors) {
              <div class="invalid-feedback">
                @if (f['title'].errors['required']) {
                  Title is required
                }
              </div>
            }
          </div>

          <div class="form-group">
            <label for="full_name">Full Name</label>
            <input 
              type="text" 
              id="full_name"
              formControlName="full_name"
              [class.is-invalid]="submitted && f['full_name'].errors"
            >
            @if (submitted && f['full_name'].errors) {
              <div class="invalid-feedback">
                @if (f['full_name'].errors['required']) {
                  Full name is required
                }
              </div>
            }
          </div>

          <div class="form-group">
            <label for="email">Email</label>
            <input 
              type="email" 
              id="email"
              formControlName="email"
              [class.is-invalid]="submitted && f['email'].errors"
            >
            @if (submitted && f['email'].errors) {
              <div class="invalid-feedback">
                @if (f['email'].errors['required']) {
                  Email is required
                }
                @if (f['email'].errors['email']) {
                  Please enter a valid email
                }
              </div>
            }
          </div>

          <div class="form-group">
            <label for="phone">Phone</label>
            <input 
              type="tel" 
              id="phone"
              formControlName="phone"
              [class.is-invalid]="submitted && f['phone'].errors"
            >
            @if (submitted && f['phone'].errors) {
              <div class="invalid-feedback">
                @if (f['phone'].errors['required']) {
                  Phone is required
                }
                @if (f['phone'].errors['pattern']) {
                  Please enter a valid phone number
                }
              </div>
            }
          </div>

          <div class="form-group">
            <label for="summary">Professional Summary</label>
            <textarea 
              id="summary"
              formControlName="summary"
              rows="4"
              [class.is-invalid]="submitted && f['summary'].errors"
            ></textarea>
            @if (submitted && f['summary'].errors) {
              <div class="invalid-feedback">
                @if (f['summary'].errors['required']) {
                  Summary is required
                }
              </div>
            }
          </div>

          <div class="form-group">
            <label for="experience">Experience</label>
            <textarea 
              id="experience"
              formControlName="experience"
              rows="6"
              [class.is-invalid]="submitted && f['experience'].errors"
            ></textarea>
            @if (submitted && f['experience'].errors) {
              <div class="invalid-feedback">
                @if (f['experience'].errors['required']) {
                  Experience is required
                }
              </div>
            }
          </div>

          <div class="form-group">
            <label for="education">Education</label>
            <textarea 
              id="education"
              formControlName="education"
              rows="4"
              [class.is-invalid]="submitted && f['education'].errors"
            ></textarea>
            @if (submitted && f['education'].errors) {
              <div class="invalid-feedback">
                @if (f['education'].errors['required']) {
                  Education is required
                }
              </div>
            }
          </div>

          <div class="form-group">
            <label for="skills">Skills</label>
            <textarea 
              id="skills"
              formControlName="skills"
              rows="4"
              [class.is-invalid]="submitted && f['skills'].errors"
            ></textarea>
            @if (submitted && f['skills'].errors) {
              <div class="invalid-feedback">
                @if (f['skills'].errors['required']) {
                  Skills are required
                }
              </div>
            }
          </div>

          <div class="button-group">
            <button type="submit" class="btn btn-primary" [disabled]="loading">
              {{ loading ? 'Saving...' : (isEditing ? 'Update' : 'Create') }}
            </button>
            <button type="button" class="btn btn-secondary" (click)="onCancel()">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .resume-form-container {
      padding: 2rem;
      background-color: #f5f5f5;
      min-height: 100vh;
    }

    .resume-form-card {
      background: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      max-width: 800px;
      margin: 0 auto;
    }

    .form-group {
      margin-bottom: 1.5rem;

      label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
      }

      input, textarea {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        
        &.is-invalid {
          border-color: #dc3545;
        }
      }

      textarea {
        resize: vertical;
      }
    }

    .invalid-feedback {
      color: #dc3545;
      font-size: 0.875rem;
      margin-top: 0.25rem;
    }

    .button-group {
      margin-top: 2rem;
      display: flex;
      gap: 1rem;

      button {
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 500;

        &:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        &.btn-primary {
          background-color: #007bff;
          color: white;

          &:hover:not(:disabled) {
            background-color: #0056b3;
          }
        }

        &.btn-secondary {
          background-color: #6c757d;
          color: white;

          &:hover:not(:disabled) {
            background-color: #545b62;
          }
        }
      }
    }
  `]
})
export class ResumeFormComponent implements OnInit {
  resumeForm: FormGroup;
  isEditing = false;
  private resumeId?: number;
  loading = false;
  submitted = false;

  constructor(
    private formBuilder: FormBuilder,
    private resumeService: ResumeService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.resumeForm = this.formBuilder.group({
      title: ['', Validators.required],
      full_name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone: ['', [Validators.required, Validators.pattern('^[0-9-+()\\s]*$')]],
      summary: ['', Validators.required],
      experience: ['', Validators.required],
      education: ['', Validators.required],
      skills: ['', Validators.required]
    });
  }

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.isEditing = true;
      this.resumeId = +id;
      this.loadResume();
    }
  }

  loadResume() {
    if (this.resumeId) {
      this.loading = true;
      this.resumeService.getResume(this.resumeId).subscribe({
        next: (resume) => {
          this.resumeForm.patchValue(resume);
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading resume:', error);
          this.loading = false;
        }
      });
    }
  }

  onSubmit() {
    this.submitted = true;

    if (this.resumeForm.invalid) {
      return;
    }

    this.loading = true;
    const resumeData = this.resumeForm.value;

    if (this.isEditing && this.resumeId) {
      this.resumeService.updateResume(this.resumeId, resumeData).subscribe({
        next: () => {
          this.router.navigate(['/resumes']);
        },
        error: (error) => {
          console.error('Error updating resume:', error);
          this.loading = false;
        }
      });
    } else {
      this.resumeService.createResume(resumeData).subscribe({
        next: () => {
          this.router.navigate(['/resumes']);
        },
        error: (error) => {
          console.error('Error creating resume:', error);
          this.loading = false;
        }
      });
    }
  }

  onCancel() {
    this.router.navigate(['/resumes']);
  }

  get f() { return this.resumeForm.controls; }
}
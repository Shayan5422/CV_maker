// src/app/resume-form/resume-form.component.ts
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormArray, AbstractControl } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common'; // necessary for *ngIf and *ngFor
import { ReactiveFormsModule } from '@angular/forms'; // necessary for [formGroup] and form control directives
import { ResumeService } from '../services/resume.service';

@Component({
  selector: 'app-resume-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './resume-form.component.html',
  styleUrls: ['./resume-form.component.scss']
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
      experience: this.formBuilder.array([this.createExperienceGroup()]),
      education: this.formBuilder.array([this.createEducationGroup()]),
      skills: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.isEditing = true;
      this.resumeId = +id;
      this.loadResume();
    }
  }

  // Getter for the main form controls
  get f() {
    return this.resumeForm.controls;
  }

  // Getter for the experience FormArray
  get experienceArray(): FormArray {
    return this.resumeForm.get('experience') as FormArray;
  }

  // Getter for the education FormArray
  get educationArray(): FormArray {
    return this.resumeForm.get('education') as FormArray;
  }

  // Create a FormGroup for a single experience record.
  createExperienceGroup(): FormGroup {
    return this.formBuilder.group({
      company: ['', Validators.required],
      position: ['', Validators.required],
      start_date: ['', Validators.required],
      end_date: ['', Validators.required],
      description: ['', Validators.required]
    });
  }

  // Create a FormGroup for a single education record.
  createEducationGroup(): FormGroup {
    return this.formBuilder.group({
      institution: ['', Validators.required],
      degree: ['', Validators.required],
      start_date: ['', Validators.required],
      end_date: ['', Validators.required],
      description: ['']
    });
  }

  addExperience(): void {
    this.experienceArray.push(this.createExperienceGroup());
  }

  removeExperience(index: number): void {
    if (this.experienceArray.length > 1) {
      this.experienceArray.removeAt(index);
    }
  }

  addEducation(): void {
    this.educationArray.push(this.createEducationGroup());
  }

  removeEducation(index: number): void {
    if (this.educationArray.length > 1) {
      this.educationArray.removeAt(index);
    }
  }

  loadResume(): void {
    if (this.resumeId) {
      this.loading = true;
      this.resumeService.getResume(this.resumeId).subscribe({
        next: (resume: any) => {
          // Patch basic fields
          this.resumeForm.patchValue({
            title: resume.title,
            full_name: resume.full_name,
            email: resume.email,
            phone: resume.phone,
            summary: resume.summary,
            skills: resume.skills
          });
          // Update experience array if available and ensure it is an array.
          if (resume.experience && Array.isArray(resume.experience)) {
            this.experienceArray.clear();
            resume.experience.forEach((exp: any) => {
              this.experienceArray.push(this.formBuilder.group({
                company: exp.company || '',
                position: exp.position || '',
                start_date: exp.start_date || '',
                end_date: exp.end_date || '',
                description: exp.description || ''
              }));
            });
          }
          // Update education array similarly.
          if (resume.education && Array.isArray(resume.education)) {
            this.educationArray.clear();
            resume.education.forEach((edu: any) => {
              this.educationArray.push(this.formBuilder.group({
                institution: edu.institution || '',
                degree: edu.degree || '',
                start_date: edu.start_date || '',
                end_date: edu.end_date || '',
                description: edu.description || ''
              }));
            });
          }
          this.loading = false;
        },
        error: error => {
          console.error('Error loading resume:', error);
          this.loading = false;
        }
      });
    }
  }

  onSubmit(): void {
    this.submitted = true;
    if (this.resumeForm.invalid) {
      return;
    }
    this.loading = true;
    const resumeData = this.resumeForm.value;
  
    // Convert experience and education arrays to strings
    resumeData.experience = JSON.stringify(resumeData.experience);
    resumeData.education = JSON.stringify(resumeData.education);
  
    if (this.isEditing && this.resumeId) {
      this.resumeService.updateResume(this.resumeId, resumeData).subscribe({
        next: () => this.router.navigate(['/resumes']),
        error: error => {
          console.error('Error updating resume:', error);
          this.loading = false;
        }
      });
    } else {
      this.resumeService.createResume(resumeData).subscribe({
        next: () => this.router.navigate(['/resumes']),
        error: error => {
          console.error('Error creating resume:', error);
          this.loading = false;
        }
      });
    }
  }
  

  onCancel(): void {
    this.router.navigate(['/resumes']);
  }
}

// src/app/resume-form/resume-form.component.ts
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormArray } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
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
  existingPhoto: string | null = null;

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
      city: ['', Validators.required],
      languages: this.formBuilder.array([this.createLanguageGroup()]),
      summary: ['', Validators.required],
      // Experience and Education fields are maintained as FormArrays
      experience: this.formBuilder.array([this.createExperienceGroup()]),
      education: this.formBuilder.array([this.createEducationGroup()]),
      // New Sections:
      skills: this.formBuilder.array([this.createSkillGroup()]),
      projects: this.formBuilder.array([this.createProjectGroup()]),
      certifications: this.formBuilder.array([this.createCertificationGroup()]),
      photo: [null]
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

  // Getters for form arrays
  get f() {
    return this.resumeForm.controls;
  }

  get experienceArray(): FormArray {
    return this.resumeForm.get('experience') as FormArray;
  }

  get educationArray(): FormArray {
    return this.resumeForm.get('education') as FormArray;
  }

  get skillsArray(): FormArray {
    return this.resumeForm.get('skills') as FormArray;
  }

  get projectsArray(): FormArray {
    return this.resumeForm.get('projects') as FormArray;
  }

  get certificationsArray(): FormArray {
    return this.resumeForm.get('certifications') as FormArray;
  }

  get languagesArray(): FormArray {
    return this.resumeForm.get('languages') as FormArray;
  }

  // Form group creators
  createExperienceGroup(): FormGroup {
    return this.formBuilder.group({
      company: ['', Validators.required],
      position: ['', Validators.required],
      start_date: ['', Validators.required],
      end_date: [''],
      is_current: [false],
      description: ['', Validators.required]
    });
  }

  createEducationGroup(): FormGroup {
    return this.formBuilder.group({
      institution: ['', Validators.required],
      degree: ['', Validators.required],
      start_date: ['', Validators.required],
      end_date: [''],
      is_current: [false],
      description: ['']
    });
  }

  createSkillGroup(): FormGroup {
    return this.formBuilder.group({
      skill: ['', Validators.required],
      proficiency: ['', Validators.required]  // For example: Beginner, Intermediate, Expert
    });
  }

  createProjectGroup(): FormGroup {
    return this.formBuilder.group({
      name: ['', Validators.required],
      description: ['', Validators.required],
      link: ['']  // Optional project URL
    });
  }

  createCertificationGroup(): FormGroup {
    return this.formBuilder.group({
      title: ['', Validators.required],
      issuer: ['', Validators.required],
      date: ['', Validators.required]
    });
  }

  createLanguageGroup(): FormGroup {
    return this.formBuilder.group({
      language: ['', Validators.required],
      proficiency: ['', Validators.required]
    });
  }

  // Methods to add or remove sections
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

  addSkill(): void {
    this.skillsArray.push(this.createSkillGroup());
  }

  removeSkill(index: number): void {
    if (this.skillsArray.length > 1) {
      this.skillsArray.removeAt(index);
    }
  }

  addProject(): void {
    this.projectsArray.push(this.createProjectGroup());
  }

  removeProject(index: number): void {
    if (this.projectsArray.length > 1) {
      this.projectsArray.removeAt(index);
    }
  }

  addCertification(): void {
    this.certificationsArray.push(this.createCertificationGroup());
  }

  removeCertification(index: number): void {
    if (this.certificationsArray.length > 1) {
      this.certificationsArray.removeAt(index);
    }
  }

  addLanguage(): void {
    this.languagesArray.push(this.createLanguageGroup());
  }

  removeLanguage(index: number): void {
    if (this.languagesArray.length > 1) {
      this.languagesArray.removeAt(index);
    }
  }

  // Parsing stored JSON strings into arrays for editing
  loadResume(): void {
    if (this.resumeId) {
      this.loading = true;
      this.resumeService.getResume(this.resumeId).subscribe({
        next: (resume: any) => {
          // Patch basic fields including photo
          this.resumeForm.patchValue({
            title: resume.title,
            full_name: resume.full_name,
            email: resume.email,
            phone: resume.phone,
            city: resume.city,
            summary: resume.summary,
            photo: resume.photo
          });

          // Set the existing photo if available
          if (resume.photo) {
            this.existingPhoto = resume.photo;
          }

          // Parse JSON fields and populate FormArrays
          this.populateFormArrayFromJSON(this.languagesArray, resume.languages, this.createLanguageGroup.bind(this));
          this.populateFormArrayFromJSON(this.experienceArray, resume.experience, this.createExperienceGroup.bind(this));
          this.populateFormArrayFromJSON(this.educationArray, resume.education, this.createEducationGroup.bind(this));
          this.populateFormArrayFromJSON(this.skillsArray, resume.skills, this.createSkillGroup.bind(this));
          this.populateFormArrayFromJSON(this.projectsArray, resume.projects, this.createProjectGroup.bind(this));
          this.populateFormArrayFromJSON(this.certificationsArray, resume.certifications, this.createCertificationGroup.bind(this));
          
          this.loading = false;
        },
        error: error => {
          console.error('Error loading resume:', error);
          this.loading = false;
        }
      });
    }
  }

  // A helper method to populate a form array from a JSON field.
  // If no data exists, it keeps the initial control.
  populateFormArrayFromJSON(formArray: FormArray, jsonData: any, createGroup: () => FormGroup): void {
    formArray.clear();
    if (jsonData) {
      try {
        const data = JSON.parse(jsonData);
        if (Array.isArray(data) && data.length > 0) {
          data.forEach((item: any) => {
            // Create a new group and patch the values
            const group = createGroup();
            group.patchValue(item);
            formArray.push(group);
          });
        } else {
          formArray.push(createGroup());
        }
      } catch (e) {
        console.error('Error parsing JSON data:', e);
        formArray.push(createGroup());
      }
    } else {
      formArray.push(createGroup());
    }
  }

  // On submit, convert FormArrays to JSON strings
  onSubmit(): void {
    this.submitted = true;
    if (this.resumeForm.invalid) {
      return;
    }
    this.loading = true;
    const resumeData = this.resumeForm.value;

    // Convert form arrays to JSON strings without double encoding
    const arrayFields = ['languages', 'experience', 'education', 'skills', 'projects', 'certifications'];
    arrayFields.forEach(field => {
      if (resumeData[field] && Array.isArray(resumeData[field])) {
        resumeData[field] = JSON.stringify(resumeData[field]);
      }
    });

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

  onFileChange(event: any): void {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        this.existingPhoto = result; // Update the displayed photo
        this.resumeForm.patchValue({
          photo: result
        });
      };
      reader.readAsDataURL(file);
    }
  }
}

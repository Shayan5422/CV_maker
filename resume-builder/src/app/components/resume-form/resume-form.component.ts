import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { Resume, Education, Experience } from '../../models/resume.model';

@Component({
  selector: 'app-resume-form',
  templateUrl: './resume-form.component.html',
  styleUrls: ['./resume-form.component.css']
})
export class ResumeFormComponent implements OnInit {
  @Input() resume?: Resume;
  @Output() saveResume = new EventEmitter<Resume>();
  resumeForm: FormGroup;

  constructor(private fb: FormBuilder) {
    this.resumeForm = this.fb.group({
      full_name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone: ['', Validators.required],
      city: ['', Validators.required],
      language: ['', Validators.required],
      title: ['', Validators.required],
      summary: ['', Validators.required],
      education: this.fb.array([]),
      experience: this.fb.array([]),
      skills: this.fb.array([])
    });
  }

  ngOnInit() {
    if (this.resume) {
      this.resumeForm.patchValue({
        full_name: this.resume.full_name,
        email: this.resume.email,
        phone: this.resume.phone,
        city: this.resume.city,
        language: this.resume.language,
        title: this.resume.title,
        summary: this.resume.summary
      });

      // Clear existing arrays
      while (this.educationArray.length) {
        this.educationArray.removeAt(0);
      }
      while (this.experienceArray.length) {
        this.experienceArray.removeAt(0);
      }
      while (this.skillsArray.length) {
        this.skillsArray.removeAt(0);
      }

      // Add new items
      this.resume.education?.forEach(edu => this.addEducation(edu));
      this.resume.experience?.forEach(exp => this.addExperience(exp));
      this.resume.skills?.forEach(skill => this.addSkill(skill));
    }
  }

  addEducation(education?: Education) {
    const educationForm = this.fb.group({
      degree: [education?.degree || '', Validators.required],
      school: [education?.school || '', Validators.required],
      field: [education?.field || '', Validators.required],
      startDate: [education?.startDate || '', Validators.required],
      endDate: [education?.endDate || '', Validators.required]
    });

    this.educationArray.push(educationForm);
  }

  addExperience(experience?: Experience) {
    const experienceForm = this.fb.group({
      title: [experience?.title || '', Validators.required],
      company: [experience?.company || '', Validators.required],
      location: [experience?.location || '', Validators.required],
      startDate: [experience?.startDate || '', Validators.required],
      endDate: [experience?.endDate || '', Validators.required],
      description: [experience?.description || '', Validators.required]
    });

    this.experienceArray.push(experienceForm);
  }

  addSkill(skill: string = '') {
    const skillControl = this.fb.control(skill, Validators.required);
    this.skillsArray.push(skillControl);
  }

  get educationArray() {
    return this.resumeForm.get('education') as FormArray;
  }

  get experienceArray() {
    return this.resumeForm.get('experience') as FormArray;
  }

  get skillsArray() {
    return this.resumeForm.get('skills') as FormArray;
  }

  onSubmit() {
    if (this.resumeForm.valid) {
      const formValue = this.resumeForm.value;
      // Convert form value to Resume type
      const resume: Resume = {
        ...formValue,
        id: this.resume?.id,
        user_id: this.resume?.user_id,
        updated_at: new Date().toISOString()
      };
      // Emit the resume data
      this.saveResume.emit(resume);
    }
  }
} 
// src/app/components/register/register.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  template: `
    <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 py-12 px-4 sm:px-6 lg:px-8 flex items-center">
      <div class="max-w-md w-full mx-auto space-y-8">
        <!-- Header -->
        <div class="text-center">
          <h2 class="text-3xl font-bold text-gray-900">Create Account</h2>
          <p class="mt-2 text-sm text-gray-600">
            Join us to create and manage your professional resumes
          </p>
        </div>

        <!-- Card Container -->
        <div class="bg-white py-8 px-4 shadow-xl sm:rounded-xl sm:px-10 space-y-6">
          <!-- Error Message -->
          @if (errorMessage) {
            <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg">
              <div class="flex">
                <div class="flex-shrink-0">
                  <i class="fas fa-exclamation-circle text-red-500"></i>
                </div>
                <div class="ml-3">
                  <p class="text-sm text-red-700">{{ errorMessage }}</p>
                </div>
              </div>
            </div>
          }

          <!-- Form -->
          <form [formGroup]="registerForm" (ngSubmit)="onSubmit()" class="space-y-6">
            <!-- Email Field -->
            <div>
              <label for="email" class="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div class="mt-1 relative rounded-md shadow-sm">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <i class="fas fa-envelope text-gray-400"></i>
                </div>
                <input
                  type="email"
                  id="email"
                  formControlName="email"
                  class="block w-full pl-10 pr-3 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  [ngClass]="{'border-red-500': submitted && f['email'].errors, 'border-gray-300': !submitted || !f['email'].errors}"
                  placeholder="you@example.com"
                >
              </div>
              @if (submitted && f['email'].errors) {
                <p class="mt-2 text-sm text-red-600 flex items-center gap-1">
                  <i class="fas fa-exclamation-circle"></i>
                  @if (f['email'].errors['required']) {
                    Email is required
                  }
                  @if (f['email'].errors['email']) {
                    Please enter a valid email address
                  }
                </p>
              }
            </div>

            <!-- Password Field -->
            <div>
              <label for="password" class="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div class="mt-1 relative rounded-md shadow-sm">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <i class="fas fa-lock text-gray-400"></i>
                </div>
                <input
                  type="password"
                  id="password"
                  formControlName="password"
                  class="block w-full pl-10 pr-3 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  [ngClass]="{'border-red-500': submitted && f['password'].errors, 'border-gray-300': !submitted || !f['password'].errors}"
                  placeholder="••••••••"
                >
              </div>
              @if (submitted && f['password'].errors) {
                <p class="mt-2 text-sm text-red-600 flex items-center gap-1">
                  <i class="fas fa-exclamation-circle"></i>
                  @if (f['password'].errors['required']) {
                    Password is required
                  }
                  @if (f['password'].errors['minlength']) {
                    Password must be at least 6 characters
                  }
                </p>
              }
            </div>

            <!-- Confirm Password Field -->
            <div>
              <label for="confirmPassword" class="block text-sm font-medium text-gray-700">
                Confirm Password
              </label>
              <div class="mt-1 relative rounded-md shadow-sm">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <i class="fas fa-lock text-gray-400"></i>
                </div>
                <input
                  type="password"
                  id="confirmPassword"
                  formControlName="confirmPassword"
                  class="block w-full pl-10 pr-3 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  [ngClass]="{'border-red-500': submitted && f['confirmPassword'].errors, 'border-gray-300': !submitted || !f['confirmPassword'].errors}"
                  placeholder="••••••••"
                >
              </div>
              @if (submitted && f['confirmPassword'].errors) {
                <p class="mt-2 text-sm text-red-600 flex items-center gap-1">
                  <i class="fas fa-exclamation-circle"></i>
                  @if (f['confirmPassword'].errors['required']) {
                    Please confirm your password
                  }
                  @if (f['confirmPassword'].errors['matching']) {
                    Passwords do not match
                  }
                </p>
              }
            </div>

            <!-- Submit Button -->
            <div>
              <button
                type="submit"
                [disabled]="loading"
                class="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200">
                @if (loading) {
                  <i class="fas fa-spinner fa-spin"></i>
                  Creating Account...
                } @else {
                  <i class="fas fa-user-plus"></i>
                  Register
                }
              </button>
            </div>
          </form>

          <!-- Login Link -->
          <div class="text-sm text-center">
            <span class="text-gray-600">Already have an account?</span>
            <a routerLink="/login" class="ml-1 font-medium text-blue-600 hover:text-blue-500 hover:underline">
              Sign in instead
            </a>
          </div>
        </div>
      </div>
    </div>
  `
})
export class RegisterComponent {
  registerForm: FormGroup;
  loading = false;
  submitted = false;
  errorMessage = '';

  constructor(
    private formBuilder: FormBuilder,
    private router: Router,
    private authService: AuthService
  ) {
    this.registerForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]]
    }, {
      validators: this.passwordMatchValidator
    });
  }

  get f() { return this.registerForm.controls; }

  private passwordMatchValidator(formGroup: FormGroup) {
    const password = formGroup.get('password');
    const confirmPassword = formGroup.get('confirmPassword');

    if (password?.value !== confirmPassword?.value) {
      confirmPassword?.setErrors({ matching: true });
    } else {
      const errors = confirmPassword?.errors;
      if (errors) {
        delete errors['matching'];
        confirmPassword?.setErrors(Object.keys(errors).length === 0 ? null : errors);
      }
    }
  }

  onSubmit() {
    this.submitted = true;
    this.errorMessage = '';

    if (this.registerForm.invalid) {
      return;
    }

    this.loading = true;
    const { email, password } = this.registerForm.value;

    this.authService.register(email, password).subscribe({
      next: () => {
        // After successful registration, log the user in
        this.authService.login(email, password).subscribe({
          next: () => {
            this.router.navigate(['/resumes']);
          },
          error: (error) => {
            this.errorMessage = 'Login failed after registration. Please try logging in manually.';
            this.loading = false;
            console.error('Login error:', error);
          }
        });
      },
      error: (error) => {
        if (error.status === 400) {
          this.errorMessage = 'Email already registered';
        } else {
          this.errorMessage = 'Registration failed. Please try again.';
        }
        this.loading = false;
        console.error('Registration error:', error);
      }
    });
  }
}
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
    <div class="register-container">
      <div class="register-card">
        <h2 class="text-center mb-4">Create Account</h2>
        
        @if (errorMessage) {
          <div class="alert alert-danger">
            {{ errorMessage }}
          </div>
        }

        <form [formGroup]="registerForm" (ngSubmit)="onSubmit()">
          <div class="form-group">
            <label for="email">Email</label>
            <input 
              type="email" 
              id="email"
              formControlName="email"
              class="form-control"
              [class.is-invalid]="submitted && f['email'].errors"
            >
            @if (submitted && f['email'].errors) {
              <div class="invalid-feedback">
                @if (f['email'].errors['required']) {
                  Email is required
                }
                @if (f['email'].errors['email']) {
                  Please enter a valid email address
                }
              </div>
            }
          </div>

          <div class="form-group">
            <label for="password">Password</label>
            <input 
              type="password" 
              id="password"
              formControlName="password"
              class="form-control"
              [class.is-invalid]="submitted && f['password'].errors"
            >
            @if (submitted && f['password'].errors) {
              <div class="invalid-feedback">
                @if (f['password'].errors['required']) {
                  Password is required
                }
                @if (f['password'].errors['minlength']) {
                  Password must be at least 6 characters
                }
              </div>
            }
          </div>

          <div class="form-group">
            <label for="confirmPassword">Confirm Password</label>
            <input 
              type="password" 
              id="confirmPassword"
              formControlName="confirmPassword"
              class="form-control"
              [class.is-invalid]="submitted && f['confirmPassword'].errors"
            >
            @if (submitted && f['confirmPassword'].errors) {
              <div class="invalid-feedback">
                @if (f['confirmPassword'].errors['required']) {
                  Please confirm your password
                }
                @if (f['confirmPassword'].errors['matching']) {
                  Passwords do not match
                }
              </div>
            }
          </div>

          <button 
            type="submit" 
            class="btn btn-primary btn-block"
            [disabled]="loading">
            {{ loading ? 'Creating Account...' : 'Register' }}
          </button>
        </form>

        <div class="text-center mt-3">
          <p>Already have an account? <a routerLink="/login">Login</a></p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .register-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background-color: #f5f5f5;
      padding: 1rem;
    }

    .register-card {
      background: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      width: 100%;
      max-width: 400px;

      h2 {
        color: #2c3e50;
        margin-bottom: 1.5rem;
      }
    }

    .form-group {
      margin-bottom: 1.5rem;

      label {
        display: block;
        margin-bottom: 0.5rem;
        color: #2c3e50;
        font-weight: 500;
      }
    }

    .form-control {
      width: 100%;
      padding: 0.75rem 1rem;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 1rem;
      transition: border-color 0.2s ease;
      
      &:focus {
        outline: none;
        border-color: #3498db;
        box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
      }

      &.is-invalid {
        border-color: #e74c3c;

        &:focus {
          box-shadow: 0 0 0 2px rgba(231, 76, 60, 0.1);
        }
      }
    }

    .invalid-feedback {
      color: #e74c3c;
      font-size: 0.875rem;
      margin-top: 0.25rem;
    }

    .alert {
      padding: 1rem;
      border-radius: 4px;
      margin-bottom: 1rem;
      font-size: 0.875rem;

      &.alert-danger {
        background-color: #fdf0ed;
        border: 1px solid #fadbd8;
        color: #c0392b;
      }
    }

    .btn {
      display: inline-block;
      padding: 0.75rem 1rem;
      font-size: 1rem;
      font-weight: 500;
      text-align: center;
      text-decoration: none;
      border-radius: 4px;
      transition: all 0.2s ease;
      cursor: pointer;
      border: none;
      width: 100%;

      &-primary {
        background-color: #3498db;
        color: white;

        &:hover:not(:disabled) {
          background-color: #2980b9;
        }

        &:disabled {
          background-color: #bdc3c7;
          cursor: not-allowed;
        }
      }
    }

    .text-center {
      text-align: center;
    }

    .mt-3 {
      margin-top: 1rem;
    }

    .mb-4 {
      margin-bottom: 1.5rem;
    }

    a {
      color: #3498db;
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }
    }
  `]
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
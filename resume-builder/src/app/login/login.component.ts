// src/app/components/login/login.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="login-container">
      <div class="login-card">
        <h2 class="text-center mb-4">Login</h2>
        
        @if (errorMessage) {
          <div class="alert alert-danger">
            {{ errorMessage }}
          </div>
        }

        <form #loginForm="ngForm" (ngSubmit)="onSubmit()">
          <div class="form-group">
            <label for="email">Email:</label>
            <input 
              type="email" 
              id="email"
              class="form-control" 
              [(ngModel)]="email" 
              name="email" 
              required 
              email
              #emailInput="ngModel">
              @if (emailInput.invalid && emailInput.touched) {
                <div class="invalid-feedback">
                  Please enter a valid email address
                </div>
              }
          </div>

          <div class="form-group">
            <label for="password">Password:</label>
            <input 
              type="password" 
              id="password"
              class="form-control" 
              [(ngModel)]="password" 
              name="password" 
              required
              minlength="6"
              #passwordInput="ngModel">
              @if (passwordInput.invalid && passwordInput.touched) {
                <div class="invalid-feedback">
                  Password must be at least 6 characters long
                </div>
              }
          </div>

          <button 
            type="submit" 
            class="btn btn-primary btn-block"
            [disabled]="loginForm.invalid || loading">
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>
        </form>

        <div class="text-center mt-3">
          <p>Don't have an account? <a routerLink="/register">Register</a></p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .login-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background-color: #f5f5f5;
    }

    .login-card {
      background: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      width: 100%;
      max-width: 400px;
    }

    .form-group {
      margin-bottom: 1rem;
    }

    label {
      display: block;
      margin-bottom: 0.5rem;
    }

    .form-control {
      width: 100%;
      padding: 0.5rem;
      border: 1px solid #ddd;
      border-radius: 4px;
      
      &.ng-invalid.ng-touched {
        border-color: #dc3545;
      }
    }

    .invalid-feedback {
      color: #dc3545;
      font-size: 0.875rem;
      margin-top: 0.25rem;
    }

    .btn-block {
      width: 100%;
    }

    .alert {
      padding: 0.75rem 1.25rem;
      margin-bottom: 1rem;
      border: 1px solid transparent;
      border-radius: 4px;

      &.alert-danger {
        color: #721c24;
        background-color: #f8d7da;
        border-color: #f5c6cb;
      }
    }

    .btn-primary {
      background-color: #007bff;
      color: white;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;

      &:disabled {
        background-color: #ccc;
        cursor: not-allowed;
      }

      &:hover:not(:disabled) {
        background-color: #0056b3;
      }
    }
  `]
})
export class LoginComponent {
  email = '';
  password = '';
  errorMessage = '';
  loading = false;

  constructor(
    private authService: AuthService,
    private router: Router
  ) { }

  onSubmit() {
    this.loading = true;
    this.errorMessage = '';
    
    this.authService.login(this.email, this.password).subscribe({
      next: () => {
        this.router.navigate(['/resumes']);
      },
      error: error => {
        this.errorMessage = 'Invalid email or password';
        console.error('Login failed:', error);
        this.loading = false;
      }
    });
  }
}
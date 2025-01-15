// src/app/components/nav/nav.component.ts
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-nav',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (authService.currentUserValue) {
      <nav class="navbar">
        <div class="navbar-container">
          <a routerLink="/resumes" class="navbar-brand">
            Resume Builder
          </a>

          <div class="navbar-menu">
            <a routerLink="/resumes" routerLinkActive="active">My Resumes</a>
            <button class="btn btn-outline" (click)="logout()">
              <i class="fas fa-sign-out-alt"></i> Logout
            </button>
          </div>
        </div>
      </nav>
    }
  `,
  styles: [`
    .navbar {
      background-color: white;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      position: sticky;
      top: 0;
      z-index: 1000;
    }

    .navbar-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .navbar-brand {
      font-size: 1.5rem;
      font-weight: 700;
      color: #2c3e50;
      text-decoration: none;
      
      &:hover {
        color: #3498db;
      }
    }

    .navbar-menu {
      display: flex;
      align-items: center;
      gap: 1.5rem;

      a {
        text-decoration: none;
        color: #666;
        font-weight: 500;
        padding: 0.5rem;
        border-radius: 4px;

        &:hover {
          color: #3498db;
        }

        &.active {
          color: #3498db;
        }
      }

      .btn-outline {
        border: 1px solid #ddd;
        color: #666;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        background: none;
        font-weight: 500;

        &:hover {
          background-color: #f8f9fa;
          border-color: #aaa;
        }

        i {
          font-size: 0.9em;
        }
      }
    }
  `]
})
export class NavComponent {
  constructor(public authService: AuthService) {}

  logout() {
    this.authService.logout();
  }
}
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, CommonModule],
  template: `
    <nav class="bg-white shadow-md sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- Logo/Brand -->
          <div class="flex-shrink-0 flex items-center">
            <a routerLink="/" 
               class="flex items-center gap-2 text-xl font-bold text-gray-800 hover:text-blue-600 transition-colors">
              <i class="fas fa-file-alt text-blue-600"></i>
              Resume Builder
            </a>
          </div>

          <!-- Navigation Links -->
          <div class="flex items-center gap-6">
            <ng-container *ngIf="authService.isAuthenticated(); else loginTemplate">
              <a routerLink="/resumes" 
                 routerLinkActive="text-blue-600"
                 class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors rounded-md">
                <i class="fas fa-folder"></i>
                My Resumes
              </a>

              <button 
                (click)="logout()"
                class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all">
                <i class="fas fa-sign-out-alt"></i>
                Logout
              </button>
            </ng-container>

            <ng-template #loginTemplate>
              <a routerLink="/login" 
                 routerLinkActive="text-blue-600"
                 class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors rounded-md">
                <i class="fas fa-sign-in-alt"></i>
                Login
              </a>
              <a routerLink="/register" 
                 routerLinkActive="text-blue-600"
                 class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all">
                <i class="fas fa-user-plus"></i>
                Register
              </a>
            </ng-template>
          </div>
        </div>
      </div>
    </nav>
  `
})
export class NavComponent {
  constructor(public authService: AuthService) {}

  logout() {
    this.authService.logout();
  }
}
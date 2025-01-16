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
      <nav class="bg-white shadow-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex justify-between items-center h-16">
            <!-- Logo/Brand -->
            <div class="flex-shrink-0 flex items-center">
              <a routerLink="/resumes" 
                 class="flex items-center gap-2 text-xl font-bold text-gray-800 hover:text-blue-600 transition-colors">
                <i class="fas fa-file-alt text-blue-600"></i>
                Resume Builder
              </a>
            </div>

            <!-- Navigation Links -->
            <div class="flex items-center gap-6">
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
            </div>
          </div>
        </div>

        <!-- Mobile Menu Button - Add if needed -->
        <!-- <div class="sm:hidden">
          <button 
            (click)="toggleMobileMenu()"
            class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500">
            <i class="fas" [class.fa-bars]="!isMobileMenuOpen" [class.fa-times]="isMobileMenuOpen"></i>
          </button>
        </div> -->

        <!-- Mobile Menu - Add if needed -->
        <!-- @if (isMobileMenuOpen) {
          <div class="sm:hidden">
            <div class="px-2 pt-2 pb-3 space-y-1">
              <a routerLink="/resumes"
                 routerLinkActive="bg-blue-50 text-blue-600"
                 class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                My Resumes
              </a>
              <button 
                (click)="logout()"
                class="w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                Logout
              </button>
            </div>
          </div>
        } -->
      </nav>
    }
  `
})
export class NavComponent {
  constructor(public authService: AuthService) {}

  logout() {
    this.authService.logout();
  }
}
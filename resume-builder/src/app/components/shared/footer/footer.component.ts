import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <footer class="bg-white border-t mt-auto">
      <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 md:flex md:items-center md:justify-between lg:px-8">
        <div class="flex justify-center space-x-4 md:order-2">
          <a href="https://buymeacoffee.com/ShayanHSHM" 
             target="_blank" 
             rel="noopener noreferrer" 
             class="px-3 py-1.5 bg-[#FFDD00] text-[#000000] rounded-lg hover:bg-[#FFCD00] transition-colors duration-200 flex items-center gap-1.5 text-sm font-medium">
            <i class="fas fa-coffee"></i>
            
          </a>
          <a href="https://linkedin.com/in/shayan-hashemi-5308081b1" 
             target="_blank" 
             rel="noopener noreferrer" 
             class="px-3 py-1.5 bg-[#0A66C2] text-white rounded-lg hover:bg-[#004182] transition-colors duration-200 flex items-center gap-1.5 text-sm font-medium">
            <i class="fab fa-linkedin"></i>
            
          </a>
          <a href="https://github.com/Shayan5422" 
             target="_blank" 
             rel="noopener noreferrer" 
             class="px-3 py-1.5 bg-[#24292F] text-white rounded-lg hover:bg-[#1B1F23] transition-colors duration-200 flex items-center gap-1.5 text-sm font-medium">
            <i class="fab fa-github"></i>
            
          </a>
        </div>
        <div class="mt-4 md:mt-0 md:order-1">
          <p class="text-center text-sm text-gray-500">
            &copy; 2025 Resume Builder. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  `,
  styles: []
})
export class FooterComponent {
  currentYear = new Date().getFullYear();
} 
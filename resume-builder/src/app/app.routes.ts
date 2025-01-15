// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./login/login.component')
      .then(m => m.LoginComponent)
  },
  {
    path: 'register',
    loadComponent: () => import('./register/register.component')
      .then(m => m.RegisterComponent)
  },
  {
    path: 'resumes',
    loadComponent: () => import('./resume-list/resume-list.component')
      .then(m => m.ResumeListComponent),
    canActivate: [authGuard]
  },
  {
    path: 'resumes/new',
    loadComponent: () => import('./resume-form/resume-form.component')
      .then(m => m.ResumeFormComponent),
    canActivate: [authGuard]
  },
  {
    path: 'resumes/edit/:id',
    loadComponent: () => import('./resume-form/resume-form.component')
      .then(m => m.ResumeFormComponent),
    canActivate: [authGuard]
  },
  {
    path: '',
    redirectTo: 'resumes',
    pathMatch: 'full'
  }
];
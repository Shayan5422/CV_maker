// src/app/interceptors/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  
  if (authService.currentUserValue?.access_token) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${authService.currentUserValue.access_token}`
      }
    });
  }
  
  return next(req);
};

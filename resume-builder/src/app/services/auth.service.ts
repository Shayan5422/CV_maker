import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private baseUrl = 'http://127.0.0.1:8000';
    private tokenKey = 'auth_token';
    private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());

    constructor(
        private http: HttpClient,
        private router: Router
    ) {
        console.log('Initial auth state:', this.isAuthenticated());
    }

    login(email: string, password: string): Observable<any> {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        return this.http.post(`${this.baseUrl}/token`, formData).pipe(
            tap((response: any) => {
                console.log('Login response:', response);
                if (response.access_token) {
                    this.setToken(response.access_token);
                    this.isAuthenticatedSubject.next(true);
                    console.log('Token stored, auth state updated');
                }
            })
        );
    }

    register(email: string, password: string): Observable<any> {
        return this.http.post(`${this.baseUrl}/register`, { email, password });
    }

    logout(): void {
        localStorage.removeItem(this.tokenKey);
        this.isAuthenticatedSubject.next(false);
        console.log('Logged out, token removed');
        this.router.navigate(['/login']);
    }

    getToken(): string | null {
        const token = localStorage.getItem(this.tokenKey);
        console.log('Retrieved token:', token ? 'exists' : 'null');
        return token;
    }

    private setToken(token: string): void {
        localStorage.setItem(this.tokenKey, token);
        console.log('Token set in localStorage');
    }

    private hasToken(): boolean {
        return !!this.getToken();
    }

    isAuthenticated(): boolean {
        const isAuth = this.hasToken();
        console.log('Checking auth state:', isAuth);
        return isAuth;
    }

    getAuthStatus(): Observable<boolean> {
        return this.isAuthenticatedSubject.asObservable();
    }

    // Handle 401 Unauthorized errors
    handleAuthError(): void {
        console.log('Handling auth error');
        localStorage.removeItem(this.tokenKey);
        this.isAuthenticatedSubject.next(false);
        this.router.navigate(['/login']);
    }
}
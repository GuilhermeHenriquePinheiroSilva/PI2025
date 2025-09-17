// services/auth.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { User } from '../app/models/user.model';
import { Enterprise } from '../app/models/enterprise.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = '/api';
  
  private userSubject = new BehaviorSubject<User | null>(this.getUserFromStorage());
  public user$: Observable<User | null> = this.userSubject.asObservable();

  constructor(private http: HttpClient) { }

  login(email: string, password: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/auth/login`, { email, password }).pipe(
      tap(response => this.handleLoginResponse(response))
    );
  }

  // NOVO MÉTODO PARA LOGIN DE EMPRESA
  loginEnterprise(email: string, password: string): Observable<any> {
    // O backend espera 'senha', então enviamos o objeto corretamente
    return this.http.post<any>(`${this.apiUrl}/enterprise/login`, { email, senha: password }).pipe(
      tap(response => this.handleLoginResponse(response))
    );
  }

  logout(): void {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    this.userSubject.next(null);
  }

  register(user: User): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, user);
  }

  registerEnterprise(enterprise: Enterprise): Observable<any> {
    return this.http.post(`${this.apiUrl}/enterprise/register`, enterprise);
  }

  // Função privada para evitar repetição de código
  private handleLoginResponse(response: any): void {
    if (response && response.access_token && response.user) {
      localStorage.setItem('authToken', response.access_token);
      localStorage.setItem('currentUser', JSON.stringify(response.user));
      this.userSubject.next(response.user);
    }
  }

  private getUserFromStorage(): User | null {
    if (typeof localStorage === 'undefined') return null;
    const user = localStorage.getItem('currentUser');
    return user ? JSON.parse(user) : null;
  }

  public getCurrentUser(): User | null {
    return this.userSubject.value;
  }
}
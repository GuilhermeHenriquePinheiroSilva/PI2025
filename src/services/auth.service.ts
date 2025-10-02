// // services/auth.service.ts

// import { Injectable } from '@angular/core';
// import { HttpClient } from '@angular/common/http';
// import { BehaviorSubject, Observable, tap } from 'rxjs';
// import { User } from '../app/models/user.model';
// import { Enterprise } from '../app/models/enterprise.model';
// import { jwtDecode } from 'jwt-decode';

// @Injectable({
//   providedIn: 'root'
// })
// export class AuthService {
//   private apiUrl = '/api';
  
//   private userSubject = new BehaviorSubject<User | null>(this.getUserFromStorage());
//   public user$: Observable<User | null> = this.userSubject.asObservable();

//   constructor(private http: HttpClient) { }

//   login(email: string, password: string): Observable<any> {
//     return this.http.post<any>(`${this.apiUrl}/auth/login`, { email, password }).pipe(
//       tap(response => this.handleLoginResponse(response))
//     );
//   }

//   // NOVO MÉTODO PARA LOGIN DE EMPRESA
//   loginEnterprise(email: string, password: string): Observable<any> {
//     // O backend espera 'senha', então enviamos o objeto corretamente
//     return this.http.post<any>(`${this.apiUrl}/enterprise/login`, { email, senha: password }).pipe(
//       tap(response => this.handleLoginResponse(response))
//     );
//   }

//   logout(): void {
//     localStorage.removeItem('authToken');
//     localStorage.removeItem('currentUser');
//     this.userSubject.next(null);
//   }

//   register(user: User): Observable<any> {
//     return this.http.post(`${this.apiUrl}/auth/register`, user);
//   }

//   registerEnterprise(enterprise: Enterprise): Observable<any> {
//     return this.http.post(`${this.apiUrl}/enterprise/register`, enterprise);
//   }

//   isAuthenticated(): boolean {
//     if (typeof localStorage === 'undefined') {
//       return false;
//     }
//     const token = localStorage.getItem('access_token');
//     return !!token; // Retorna true se o token existir, false caso contrário
//   }

//   getUserRole(): string | null {
//     if (typeof localStorage === 'undefined') {
//       return null;
//     }
//     const token = localStorage.getItem('access_token');
//     if (token) {
//       try {
//         const decodedToken: any = jwtDecode(token);
//         return decodedToken.role; 
//       } catch (error) {
//         console.error("Erro ao decodificar o token:", error);
//         return null;
//       }
//     }
//     return null;
//   }

//   // Função privada para evitar repetição de código
//   private handleLoginResponse(response: any): void {
//     if (response && response.access_token && response.user) {
//       localStorage.setItem('authToken', response.access_token);
//       localStorage.setItem('currentUser', JSON.stringify(response.user));
//       this.userSubject.next(response.user);
//     }
//   }

//   private getUserFromStorage(): User | null {
//     if (typeof localStorage === 'undefined') return null;
//     const user = localStorage.getItem('currentUser');
//     return user ? JSON.parse(user) : null;
//   }

//   public getCurrentUser(): User | null {
//     return this.userSubject.value;
//   }
// }

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { User } from '../app/models/user.model';
import { Enterprise } from '../app/models/enterprise.model';
import { jwtDecode } from 'jwt-decode';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = '/api';

  private loggedIn = new BehaviorSubject<boolean>(this.hasTokenInStorage());
  private userRole = new BehaviorSubject<string | null>(this.getRoleFromStorage());
  private userSubject = new BehaviorSubject<User | null>(this.getUserFromStorage());
  public user$: Observable<User | null> = this.userSubject.asObservable();

  constructor(private http: HttpClient) { }

  login(email: string, password: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/auth/login`, { email, password }).pipe(
      tap(response => this.handleLoginResponse(response))
    );
  }

  forgotPassword(email: string): Observable<{message: string}> {
    // A rota correta é /users/forgot-password
    return this.http.post<{message: string}>(`${this.apiUrl}/auth/forgot-password`, { email });
  }

  resetPassword(token: string, new_password: string): Observable<{message: string}> {
    // A rota correta é /users/reset-password
    return this.http.post<{message: string}>(`${this.apiUrl}/auth/reset-password`, { token, new_password });
  }

  loginEnterprise(email: string, password: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/enterprise/login`, { email, senha: password }).pipe(
      tap(response => this.handleLoginResponse(response))
    );
  }

  logout(): void {
    // Limpa o localStorage
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    // Atualiza os sujeitos de estado para refletir o logout
    this.userSubject.next(null);
    this.loggedIn.next(false);
    this.userRole.next(null);
  }

  register(user: User): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, user);
  }

  registerEnterprise(enterprise: Enterprise): Observable<any> {
    return this.http.post(`${this.apiUrl}/enterprise/register`, enterprise);
  }

  // --- MÉTODOS ATUALIZADOS PARA O ADMIN GUARD ---
  // Retorna o valor ATUAL do estado de login. É síncrono e confiável.
  isAuthenticated(): boolean {
    return this.loggedIn.getValue();
  }

  // Retorna a role ATUAL do usuário. Síncrono e confiável.
  getUserRole(): string | null {
    return this.userRole.getValue();
  }

  verifyEmail(token: string): Observable<{message: string}> {
    return this.http.get<{message: string}>(`${this.apiUrl}/auth/verify-email?token=${token}`);
  }

  // --- FUNÇÕES PRIVADAS DE MANIPULAÇÃO ---
  private handleLoginResponse(response: any): void {
    if (response && response.access_token && response.user) {
      // 1. Salva no localStorage
      localStorage.setItem('authToken', response.access_token);
      localStorage.setItem('currentUser', JSON.stringify(response.user));
      
      // 2. ATUALIZA OS SUJEITOS DE ESTADO IMEDIATAMENTE
      this.userSubject.next(response.user);
      this.loggedIn.next(true);
      // Garante que a role seja minúscula para consistência
      this.userRole.next(response.user.role.toLowerCase()); 
    }
  }

  // --- Funções para inicializar o serviço ao carregar a página ---
  private getUserFromStorage(): User | null {
    if (typeof localStorage === 'undefined') return null;
    const user = localStorage.getItem('currentUser');
    return user ? JSON.parse(user) : null;
  }

  private hasTokenInStorage(): boolean {
    if (typeof localStorage === 'undefined') return false;
    return !!localStorage.getItem('authToken');
  }

  private getRoleFromStorage(): string | null {
    if (typeof localStorage === 'undefined') return null;
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const decodedToken: any = jwtDecode(token);
        return decodedToken.role ? decodedToken.role.toLowerCase() : null;
      } catch (error) {
        console.error("Erro ao decodificar o token:", error);
        return null;
      }
    }
    return null;
  }

  public getCurrentUser(): User | null {
    return this.userSubject.value;
  }
}
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserDetails {
  username: string;
  email: string;
  account_type: 'person' | 'enterprise'; // Tipo da conta
  cpf?: string;
  cnpj?: string;
  role: 'CUSTOMER' | 'ENTERPRISE' | 'ADMIN'; // Role atual
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private apiUrl = '/api/auth';

  constructor(private http: HttpClient) { }

  // busca os dados do usuário logado
  getMe(): Observable<UserDetails> {
    return this.http.get<UserDetails>(`${this.apiUrl}/me`);
  }
}
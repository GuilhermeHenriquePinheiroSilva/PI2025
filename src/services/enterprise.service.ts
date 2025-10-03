import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Enterprise, EnterpriseFormData } from '../app/models/enterprise.model';

@Injectable({
  providedIn: 'root'
})
export class EnterpriseService {
  // A URL base da sua API. O proxy.conf.json deve redirecionar as chamadas.
  private apiUrl = '/api/enterprise';

  constructor(private http: HttpClient) { }

  registerEnterprise(enterpriseData: EnterpriseFormData): Observable<Enterprise> {
    return this.http.post<Enterprise>(`${this.apiUrl}/register`, enterpriseData);
  }

  getPendingEnterprises(): Observable<Enterprise[]> {
    return this.http.get<Enterprise[]>(`${this.apiUrl}/pending`);
  }

  approveEnterprise(id: number): Observable<Enterprise> {
    return this.http.put<Enterprise>(`${this.apiUrl}/${id}/approve`, {});
  }

  rejectEnterprise(id: number, reason: string): Observable<Enterprise> {
    // Agora enviamos o motivo no corpo da requisição
    const body = { rejection_reason: reason };
    return this.http.put<Enterprise>(`${this.apiUrl}/${id}/reject`, body);
  }
}
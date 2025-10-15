import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Enterprise, EnterpriseFormData } from '../app/models/enterprise.model';

@Injectable({
  providedIn: 'root'
})
export class EnterpriseService {
  private apiUrl = '/api/enterprise';

  constructor(private http: HttpClient) { }

  registerEnterprise(enterpriseData: EnterpriseFormData): Observable<Enterprise> {
    return this.http.post<Enterprise>(`${this.apiUrl}/register`, enterpriseData);
  }

  getEnterprisesByStatus(status: 'PENDING' | 'APPROVED' | 'REJECTED'): Observable<Enterprise[]> {
    const endpoint = `${this.apiUrl}/${status.toLowerCase()}`;
    return this.http.get<Enterprise[]>(endpoint);
  }

  approveEnterprise(id: number): Observable<Enterprise> {
    return this.http.put<Enterprise>(`${this.apiUrl}/${id}/approve`, {});
  }

  rejectEnterprise(id: number, reason: string): Observable<Enterprise> {
    const body = { rejection_reason: reason };
    return this.http.put<Enterprise>(`${this.apiUrl}/${id}/reject`, body);
  }

  getMyEnterprise(): Observable<Enterprise> {
    return this.http.get<Enterprise>(`${this.apiUrl}/me`);
  }
}
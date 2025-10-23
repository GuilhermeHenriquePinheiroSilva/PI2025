import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Enterprise, EnterpriseFormData } from '../app/models/enterprise.model';
import { OrderItem } from '../app/models/order.model';

export interface DashboardStats {
  total_sales_count: number;
  total_sales_value: number; // Backend envia como Decimal, mas TypeScript pode tratar como number
  total_products_count: number;
  total_stock_count: number;
}

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

  getEnterpriseSalesHistory(productId?: string, month?: number, year?: number): Observable<OrderItem[]> {
    let params = new HttpParams();
    if (productId) {
      params = params.set('product_id', productId);
    }
    if (month) {
      params = params.set('month', month.toString());
    }
    if (year) {
      params = params.set('year', year.toString());
    }
    // CORREÇÃO DA URL AQUI:
    return this.http.get<OrderItem[]>(`${this.apiUrl}/enterprise/sales`, { params }); // Usa this.apiUrl que é /api/enterprise
  }

  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.apiUrl}/dashboard-stats`);
  }
}
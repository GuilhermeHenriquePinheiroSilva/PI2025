import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Order } from '../app/models/order.model'; // Importe o novo modelo

@Injectable({
  providedIn: 'root'
})
export class OrderService {
  private apiUrl = '/api/orders';

  constructor(private http: HttpClient) { }

  getMyOrders(): Observable<Order[]> {
    return this.http.get<Order[]>(`${this.apiUrl}/me`);
  }
}
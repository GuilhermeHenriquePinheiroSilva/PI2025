import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CartItem } from './cart.service';

// Interface para a resposta da criação da preferência
export interface PreferenceResponse {
  preference_id: string;
  init_point: string;
}

@Injectable({
  providedIn: 'root'
})
export class PurchaseService {
  // A URL base agora aponta para o endpoint do Mercado Pago no seu backend
  private apiUrl = '/api/mercadopago';

  constructor(private http: HttpClient) { }

  /**
   * Envia os itens do carrinho para o backend para criar uma preferência de pagamento no Mercado Pago.
   * @param items Os itens do carrinho.
   */
  createCartPreference(items: CartItem[]): Observable<PreferenceResponse> {
    const body = {
      items: items.map(item => ({
        product_id: item.product.id,
        quantity: item.quantity
      }))
    };
    return this.http.post<PreferenceResponse>(`${this.apiUrl}/create_preference_cart`, body);
  }
}
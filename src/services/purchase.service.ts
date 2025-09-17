// src/services/purchase.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CartItem } from './cart.service'; // Importe a interface CartItem

// --- Interfaces ---
export interface GiftCardInfo {
    title: string;
    valor: number;
    imageUrl?: string;
}

export interface SoldGiftCard {
    id: string;
    code: string;
    status: 'VALID' | 'USED' | 'EXPIRED';
    purchase_date: string;
    register_giftcard_id: string;
    owner_id: number;
    original_giftcard: GiftCardInfo;
}

export interface MercadoPagoPreference {
    preference_id: string;
    init_point: string;
}

@Injectable({
  providedIn: 'root'
})
export class PurchaseService {
  private actionsApiUrl = '/api/actions';
  private mercadoPagoApiUrl = '/api/mercadopago';

  constructor(private http: HttpClient) { }

  /**
   * Cria uma preferência de pagamento para um ÚNICO item.
   */
  createMercadoPagoPreference(giftcardId: string, quantity: number): Observable<MercadoPagoPreference> {
    const params = new HttpParams().set('quantity', quantity.toString());
    return this.http.post<MercadoPagoPreference>(`${this.mercadoPagoApiUrl}/create_preference/${giftcardId}`, {}, { params });
  }

  createCartPreference(cartItems: CartItem[]): Observable<MercadoPagoPreference> {
    // Transforma os itens do carrinho para o formato que o backend espera
    const payload = {
      items: cartItems.map(item => ({
        product_id: item.product.id,
        quantity: item.quantity
      }))
    };
    // Chama o novo endpoint do backend que criamos
    return this.http.post<MercadoPagoPreference>(`${this.mercadoPagoApiUrl}/create_preference_cart`, payload);
  }


  getMyPurchases(): Observable<SoldGiftCard[]> {
    return this.http.get<SoldGiftCard[]>(`${this.actionsApiUrl}/my-purchases`);
  }

  validateCode(code: string): Observable<any> {
    return this.http.post(`${this.actionsApiUrl}/validate/${code}`, {});
  }

  // A função purchaseGiftCard parece ter sido substituída pelo fluxo do Mercado Pago
  // Se não estiver sendo usada, pode ser removida no futuro.
  /*
  purchaseGiftCard(giftcardId: string, quantity: number): Observable<SoldGiftCard[]> {
    const params = new HttpParams().set('quantity', quantity.toString());
    return this.http.post<SoldGiftCard[]>(`${this.actionsApiUrl}/purchase/${giftcardId}`, {}, { params });
  }
  */
}
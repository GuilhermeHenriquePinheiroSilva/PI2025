import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Category } from '../app/models/category.model';
import { OrderItem } from '../app/models/order.model';

const MP_FEE_PERCENTAGE = 0.05; // 5%
const MP_FEE_FIXED = 0.60;      // R$ 0,60
const PLATFORM_COMMISSION_PERCENTAGE = 0.10; // 10%

export interface GiftCard {
  id: string; 
  user_id: number;
  title: string;
  valor: number; 
  desired_amount: number;
  description: string;
  quantityavailable: number;
  generaterandomly: boolean;
  codes: string;
  imageUrl: string;
  ativo: boolean;
  validade: string;
  nota: number;
  category_id?: number;
  category?: Category;
}

export interface SoldGiftCardDetails {
  id: string;
  code: string;
  status: 'VALID' | 'USED' | 'EXPIRED' | 'PENDING';
  purchase_date: string;
  owner_name: string;
  original_giftcard: {
    title: string;
    valor: number;
    imageUrl: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class GiftcardService {
  private apiUrl = '/api/giftcards/';
  private validationApiUrl = '/api/validation';

  constructor(private http: HttpClient) { }

calculateSellingPrice(desiredAmount: number): number {
    if (desiredAmount <= 0) {
      return 0;
    }

    // Garante que a comissão não seja 100% ou mais
    if (PLATFORM_COMMISSION_PERCENTAGE >= 1) {
         console.error("A comissão da plataforma não pode ser 100% ou mais.");
         return 0; // Ou lance um erro
    }
    const amountBeforeMp = desiredAmount / (1 - PLATFORM_COMMISSION_PERCENTAGE);

    // Garante que a taxa do MP não seja 100% ou mais
    if (MP_FEE_PERCENTAGE >= 1) {
        console.error("A taxa percentual do MP não pode ser 100% ou mais.");
        return 0; // Ou lance um erro
    }
    const sellingPrice = (amountBeforeMp + MP_FEE_FIXED) / (1 - MP_FEE_PERCENTAGE);

    // Arredonda para 2 casas decimais
    return Math.round(sellingPrice * 100) / 100;
  }

  getMyGiftCards(): Observable<GiftCard[]> {
    return this.http.get<GiftCard[]>(`${this.apiUrl}me`);
  }

  createGiftCard(giftCardData: FormData): Observable<any> {
    return this.http.post(this.apiUrl, giftCardData);
  }

searchGiftCards(term: string, categoryId?: number, minPrice?: number, maxPrice?: number, sortBy?: string): Observable<GiftCard[]> {
    let params = new HttpParams();
    if (term) {
      params = params.set('q', term);
    }
    if (categoryId) {
      params = params.set('category_id', categoryId.toString());
    }
    // Os filtros de preço agora devem se basear no 'valor' (preço de venda)
    if (minPrice !== undefined) {
      params = params.set('min_price', minPrice.toString());
    }
    if (maxPrice !== undefined) {
      params = params.set('max_price', maxPrice.toString());
    }
    if (sortBy) {
      params = params.set('sort_by', sortBy);
    }
    return this.http.get<GiftCard[]>(`${this.apiUrl}search/`, { params });
  }

  getAllGiftCards(): Observable<GiftCard[]> {
    return this.http.get<GiftCard[]>(this.apiUrl);
  }

  getGiftCardById(id: string): Observable<GiftCard> {
    return this.http.get<GiftCard>(`${this.apiUrl}${id}`);
  }

  getTopRatedGiftCards(): Observable<GiftCard[]> {
    return this.http.get<GiftCard[]>(`${this.apiUrl}top-rated/`);
  }

  deleteGiftCard(giftCardId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}${giftCardId}`);
  }

  updateGiftCard(id: string, giftCardData: FormData): Observable<any> {
    return this.http.put(`${this.apiUrl}${id}`, giftCardData);
  }

  validateGiftCard(code: string): Observable<SoldGiftCardDetails> {
    return this.http.get<SoldGiftCardDetails>(`${this.apiUrl}validate/${code}`);
  }

  markGiftCardAsUsed(code: string): Observable<SoldGiftCardDetails> {
    return this.http.put<SoldGiftCardDetails>(`${this.apiUrl}validate/${code}/use`, {});
  }

  getUsedGiftCards(): Observable<SoldGiftCardDetails[]> {
    return this.http.get<SoldGiftCardDetails[]>(`${this.apiUrl}used/me`);
  }

  getGiftCardsByCategory(categoryId: number): Observable<GiftCard[]> {
    return this.http.get<GiftCard[]>(`${this.apiUrl}/category/${categoryId}`);
  }

  validateGiftCardCode(code: string): Observable<OrderItem> {
    return this.http.get<OrderItem>(`${this.validationApiUrl}/${code}`);
  }

  markGiftCardCodeAsUsed(code: string): Observable<OrderItem> {
    return this.http.put<OrderItem>(`${this.validationApiUrl}/${code}/use`, {});
  }

  getUsedGiftCardsHistory(): Observable<OrderItem[]> {
    return this.http.get<OrderItem[]>(`${this.validationApiUrl}/history/me`);
  }
}
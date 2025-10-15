import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Category } from '../app/models/category.model';
import { OrderItem } from '../app/models/order.model';

export interface GiftCard {
  id: string; 
  user_id: number;
  title: string;
  valor: number;
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
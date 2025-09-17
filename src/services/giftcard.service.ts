import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

// A interface define a "forma" dos dados de um Gift Card
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
}

@Injectable({
  providedIn: 'root'
})
export class GiftcardService {
  private apiUrl = '/api/giftcards/';

  constructor(private http: HttpClient) { }
  getMyGiftCards(): Observable<GiftCard[]> {
    return this.http.get<GiftCard[]>(`${this.apiUrl}me`);
  }

  createGiftCard(giftCardData: FormData): Observable<any> {
    return this.http.post(this.apiUrl, giftCardData);
  }

  searchGiftCards(term: string): Observable<GiftCard[]> {
    const params = new HttpParams().set('q', term);
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
}
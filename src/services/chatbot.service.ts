import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatbotService {

  private apiUrl = '/api/chatbot/ask'; 

  constructor(private http: HttpClient) { }

  sendMessage(message: string, history: any[]): Observable<any> {
    return this.http.post<any>(this.apiUrl, { message, history });
  }
}
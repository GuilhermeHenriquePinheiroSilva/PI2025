import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { User } from '../app/models/user.model';


@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private apiUrl = 'http://127.0.0.1:8080/register'; // URL do backend Rust

  constructor(private http: HttpClient) {}

  register(user: User): Observable<any> {
    return this.http.post<any>(this.apiUrl, user);
  }
}

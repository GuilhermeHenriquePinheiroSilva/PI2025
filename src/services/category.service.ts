import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

// Criamos uma interface para tipar os dados da categoria
export interface Category {
  id: number;
  name: string;
}

@Injectable({
  providedIn: 'root'
})
export class CategoryService {
  private apiUrl = '/api/categories/'; // A URL base da nossa API de categorias

  constructor(private http: HttpClient, private authService: AuthService) { }

  // Método para buscar todas as categorias (público)
  getCategories(): Observable<Category[]> {
    return this.http.get<Category[]>(this.apiUrl);
  }

  // Método para criar uma nova categoria (requer token de admin)
  createCategory(name: string): Observable<Category> {
    return this.http.post<Category>(this.apiUrl, { name });
  }

  // Método para atualizar uma categoria (requer token de admin)
  updateCategory(id: number, name: string): Observable<Category> {
    return this.http.put<Category>(`${this.apiUrl}/${id}`, { name });
  }

  // Método para deletar uma categoria (requer token de admin)
  deleteCategory(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}`);
  }
}
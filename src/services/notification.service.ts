// src/services/notification.service.ts
import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

export interface Notification {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info' | 'remove'; // Adicione 'remove' aqui
  id: number;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notificationSubject = new Subject<Notification>();
  private currentId = 0;
  notifications$ = this.notificationSubject.asObservable();

  constructor() { }

  show(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info', duration: number = 3000): void {
    const id = this.currentId++;
    const notification: Notification = { message, type, id };
    this.notificationSubject.next(notification);

    setTimeout(() => {
      this.remove(id);
    }, duration);
  }

  remove(id: number): void {
    // Agora enviamos uma notificação com o tipo 'remove' e o ID para o componente remover
    this.notificationSubject.next({ message: '', type: 'remove', id: id });
  }
}
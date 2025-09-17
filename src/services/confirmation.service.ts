// src/app/services/confirmation.service.ts
import { Injectable } from '@angular/core';
import { Subject, Observable } from 'rxjs';

export interface ConfirmationConfig {
  message: string;
  title?: string;
  confirmText?: string;
  cancelText?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ConfirmationService {
  private confirmationSubject = new Subject<ConfirmationConfig & { resolve: (value: boolean) => void }>();
  
  constructor() { }

  confirm(config: ConfirmationConfig): Observable<boolean> {
    return new Observable<boolean>(observer => {
      this.confirmationSubject.next({
        ...config,
        resolve: (value: boolean) => {
          observer.next(value);
          observer.complete();
        }
      });
    });
  }

  resolveConfirmation(value: boolean, configId?: number) {
  }
  get config$(): Observable<ConfirmationConfig & { resolve: (value: boolean) => void }> {
    return this.confirmationSubject.asObservable();
  }
}
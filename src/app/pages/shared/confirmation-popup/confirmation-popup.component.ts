// src/app/shared/confirmation-popup/confirmation-popup.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ConfirmationService, ConfirmationConfig } from '../../../../services/confirmation.service'; // Ajuste o caminho conforme necessário
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-confirmation-popup',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './confirmation-popup.component.html',
  styleUrl: './confirmation-popup.component.css'
})
export class ConfirmationPopupComponent implements OnInit, OnDestroy {
  isVisible: boolean = false;
  currentConfig: ConfirmationConfig | null = null;
  private resolvePromise!: (value: boolean) => void;
  private subscription!: Subscription;

  constructor(private confirmationService: ConfirmationService) {}

  ngOnInit(): void {
    this.subscription = this.confirmationService.config$.subscribe(config => {
      this.currentConfig = config;
      this.resolvePromise = config.resolve;
      this.isVisible = true;
    });
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  onConfirm(): void {
    this.resolvePromise(true);
    this.hide();
  }

  onCancel(): void {
    this.resolvePromise(false);
    this.hide();
  }

  hide(): void {
    this.isVisible = false;
    this.currentConfig = null;
  }
}
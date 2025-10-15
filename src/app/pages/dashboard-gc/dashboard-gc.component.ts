import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { GiftcardService, GiftCard } from '../../../services/giftcard.service';
import { NotificationService } from '../../../services/notification.service';
import { ConfirmationService } from '../../../services/confirmation.service';
import { FormsModule } from '@angular/forms';
import { OrderItem } from '../../models/order.model';

@Component({
  selector: 'app-dashboard-gc',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, DatePipe],
  templateUrl: './dashboard-gc.component.html',
  styleUrls: ['./dashboard-gc.component.css']
})
export class DashboardGcComponent implements OnInit {
  activeComponent = 'componente1';
  
  myGiftCards: GiftCard[] = [];
  isLoading = true;

  // Propriedades para validação
  validationCode: string = '';
  validationResult: OrderItem | null = null;
  isValidating: boolean = false;
  isPopupVisible = false;
  
  // Propriedades para o histórico
  usedItemsHistory: OrderItem[] = [];
  isLoadingHistory: boolean = false;

  constructor(
    private giftcardService: GiftcardService,
    private notificationService: NotificationService,
    private confirmationService: ConfirmationService
  ) { }

  ngOnInit(): void {
    this.loadMyGiftCards();
    this.loadUsedItemsHistory();
  }

  // --- FUNÇÃO CORRIGIDA ---
  // A função agora aceita apenas um argumento, como no HTML.
  showComponent(name: string) {
    this.activeComponent = name;
  }

  loadMyGiftCards(): void {
    this.isLoading = true;
    this.giftcardService.getMyGiftCards().subscribe({
      next: (data) => {
        this.myGiftCards = data;
        this.isLoading = false;
      },
      error: () => {
        this.notificationService.show('Não foi possível carregar seus gift cards.', 'error');
        this.isLoading = false;
      }
    });
  }

  deleteGiftCard(id: string, title: string): void {
    this.confirmationService.confirm({
      title: 'Confirmação de Exclusão',
      message: `Tem certeza que deseja excluir o gift card "${title}"?`,
      confirmText: 'Excluir',
      cancelText: 'Manter'
    }).subscribe(confirmed => {
      if (confirmed) {
        this.giftcardService.deleteGiftCard(id).subscribe({
          next: () => {
            this.notificationService.show('Gift card excluído!', 'success');
            this.myGiftCards = this.myGiftCards.filter(gc => gc.id !== id);
          },
          error: () => {
            this.notificationService.show('Falha ao excluir o gift card.', 'error');
          }
        });
      }
    });
  }

  loadUsedItemsHistory(): void {
    this.isLoadingHistory = true;
    this.giftcardService.getUsedGiftCardsHistory().subscribe({
      next: (data) => {
        this.usedItemsHistory = data;
        this.isLoadingHistory = false;
      },
      error: () => {
        this.notificationService.show('Não foi possível carregar o histórico.', 'error');
        this.isLoadingHistory = false;
      }
    });
  }

  validateCode(): void {
    if (!this.validationCode.trim()) {
      this.notificationService.show('Por favor, insira um código.', 'warning');
      return;
    }
    this.isValidating = true;
    
    this.giftcardService.validateGiftCardCode(this.validationCode).subscribe({
      next: (data) => {
        this.validationResult = data;
        this.isPopupVisible = true;
        this.isValidating = false;
      },
      error: (err) => {
        this.notificationService.show(err.error.detail || 'Código inválido ou já utilizado.', 'error');
        this.isValidating = false;
      }
    });
  }

  markAsUsed(): void {
    if (!this.validationResult) return;

    this.giftcardService.markGiftCardCodeAsUsed(this.validationCode).subscribe({
      next: () => {
        this.notificationService.show('Código marcado como utilizado!', 'success');
        this.closePopup();
        this.loadUsedItemsHistory();
      },
      error: (err) => {
        this.notificationService.show(err.error.detail, 'error');
      }
    });
  }

  closePopup(): void {
    this.isPopupVisible = false;
    this.validationResult = null;
    this.validationCode = '';
  }
}
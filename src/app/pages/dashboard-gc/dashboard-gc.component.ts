import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { GiftcardService, GiftCard, SoldGiftCardDetails } from '../../../services/giftcard.service';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { NotificationService } from '../../../services/notification.service';
import { ConfirmationService } from '../../../services/confirmation.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-dashboard-gc',
  standalone: true,
  imports: [CommonModule, RouterLink, NavBarComponent, FooterComponent, FormsModule],
  templateUrl: './dashboard-gc.component.html',
  styleUrl: './dashboard-gc.component.css'
})
export class DashboardGcComponent implements OnInit {
  activeComponent = 'componente1';

  @ViewChild('underline') underline!: ElementRef<HTMLDivElement>;
  @ViewChild('navBar') navBar!: ElementRef<HTMLDivElement>;
  @ViewChild('btn1') btn1!: ElementRef<HTMLButtonElement>;
  @ViewChild('btn2') btn2!: ElementRef<HTMLButtonElement>;
  @ViewChild('btn3') btn3!: ElementRef<HTMLButtonElement>;

  validationCode: string = '';
  validationResult: SoldGiftCardDetails | null = null;
  isValidating: boolean = false;
  validationError: string | null = null;

  isPopupVisible = false;
  usedGiftCards: SoldGiftCardDetails[] = [];
  isLoadingHistory: boolean = false;

  ngAfterViewInit() {
  }

  showComponent(name: string, button: HTMLButtonElement) {
    this.activeComponent = name;
  }

  myGiftCards: GiftCard[] = [];
  isLoading: boolean = true;

  constructor(
    private giftcardService: GiftcardService,
    private notificationService: NotificationService,
    private confirmationService: ConfirmationService
  ) { }

  ngOnInit(): void {
    this.loadMyGiftCards();
    this.loadUsedGiftCards();
  }

  

  loadMyGiftCards(): void {
    this.isLoading = true;

    this.giftcardService.getMyGiftCards().subscribe({
      next: (data) => {
        this.myGiftCards = data;
        this.isLoading = false;
        console.log('Gift cards do usuário carregados:', this.myGiftCards);
      },
      error: (err) => {
        console.error('Erro ao carregar os gift cards do usuário:', err);
        this.isLoading = false;
        this.notificationService.show('Não foi possível carregar seus gift cards. Verifique se você está logado.', 'error');
      }
    });
  }

  deleteGiftCard(id: string, title: string): void {
    this.confirmationService.confirm({
      title: 'Confirmação de Exclusão',
      message: `Tem certeza que deseja excluir o gift card "${title}"? Esta ação é irreversível.`,
      confirmText: 'Excluir',
      cancelText: 'Manter'
    }).subscribe(confirmed => {
      if (confirmed) {
        this.giftcardService.deleteGiftCard(id).subscribe({
          next: () => {
            this.notificationService.show('Gift card excluído com sucesso!', 'success');
            this.myGiftCards = this.myGiftCards.filter(gc => gc.id !== id);
          },
          error: (err) => {
            console.error('Erro ao excluir gift card:', err);
            this.notificationService.show('Falha ao excluir o gift card.', 'error');
          }
        });
      } else {
        this.notificationService.show('Exclusão cancelada.', 'info');
      }
    });
  }

   loadUsedGiftCards(): void {
    this.isLoadingHistory = true;
    this.giftcardService.getUsedGiftCards().subscribe({
      next: (data) => {
        this.usedGiftCards = data;
        this.isLoadingHistory = false;
      },
      error: (err) => {
        console.error('Erro ao carregar histórico de gift cards:', err);
        this.isLoadingHistory = false;
        this.notificationService.show('Não foi possível carregar o histórico de validações.', 'error');
      }
    });
  }

  validateCode(): void {
    if (!this.validationCode.trim()) {
      this.notificationService.show('Por favor, insira um código para validar.', 'error');
      return;
    }
    this.isValidating = true;
    this.validationResult = null;
    this.validationError = null;
    
    this.giftcardService.validateGiftCard(this.validationCode).subscribe({
      next: (data) => {
        this.validationResult = data;
        this.isPopupVisible = true; // Abrir o popup
        this.isValidating = false;
        this.validationCode = ''; // Limpar o campo
      },
      error: (err) => {
        this.validationError = err.error.detail || 'Código não encontrado ou inválido.';
        this.notificationService.show(this.validationError!, 'error');
        this.isValidating = false;
      }
    });
  }

  markAsUsed(): void {
    if (!this.validationResult) return;

    this.giftcardService.markGiftCardAsUsed(this.validationResult.code).subscribe({
      next: (data) => {
        this.validationResult = data; // Atualiza o status no popup
        this.notificationService.show('Gift Card marcado como utilizado!', 'success');
        this.loadUsedGiftCards(); // Recarrega o histórico
      },
      error: (err) => {
        this.notificationService.show(err.error.detail || 'Não foi possível marcar o gift card como utilizado.', 'error');
      }
    });
  }

  closePopup(): void {
    this.isPopupVisible = false;
    this.validationResult = null;
  }
}

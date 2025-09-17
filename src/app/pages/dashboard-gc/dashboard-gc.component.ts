import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { GiftcardService, GiftCard } from '../../../services/giftcard.service';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { NotificationService } from '../../../services/notification.service';
import { ConfirmationService } from '../../../services/confirmation.service';

@Component({
  selector: 'app-dashboard-gc',
  standalone: true,
  imports: [CommonModule, RouterLink, NavBarComponent, FooterComponent],
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
}

import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddGcComponent } from './add-gc.component';

describe('AddGcComponent', () => {
  let component: AddGcComponent;
  let fixture: ComponentFixture<AddGcComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddGcComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AddGcComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

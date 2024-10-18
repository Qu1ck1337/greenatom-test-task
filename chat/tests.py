from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from chat.models import User, Channel


class ChannelAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass1234')
        self.second_user = User.objects.create_user(username='testuser2', password='testpass1234')

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

    def test_create_channel(self):
        # Success create
        data = {
            'name': 'Test Channel'
        }
        response = self.client.post(reverse('channel-list'), data=data)
        channel_obj = Channel.objects.get()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Channel.objects.count(), 1)
        self.assertEqual(channel_obj.name, data['name'])
        self.assertEqual(channel_obj.owner, self.user)
        self.assertEqual(channel_obj.members.all().count(), 1)
        self.assertEqual(channel_obj.members.first(), self.user)
        self.assertEqual(channel_obj.black_list.count(), 0)

        # Black list added member check
        data = {
            'name': 'Test Channel 2',
            'black_list': [self.second_user.pk]
        }
        response = self.client.post(reverse('channel-list'), data=data)
        channel_obj = Channel.objects.get(name=data['name'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(channel_obj.owner, self.user)
        self.assertEqual(channel_obj.members.all().count(), 1)
        self.assertEqual(channel_obj.members.first(), self.user)
        self.assertEqual(channel_obj.black_list.count(), 1)
        self.assertEqual(channel_obj.black_list.first(), self.second_user)

    def test_list_channels(self):
        Channel.objects.create(name='Test Channel', owner=self.user)
        Channel.objects.create(name='Test Channel 2', owner=self.user)

        response = self.client.get(reverse('channel-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Test Channel')
        self.assertEqual(response.data[1]['name'], 'Test Channel 2')

    def test_retrieve_channel(self):
        channel = Channel.objects.create(name='Test Channel', owner=self.user)
        url = reverse('channel-detail', kwargs={'pk': channel.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Channel')

    def test_update_channel(self):
        channel = Channel.objects.create(name='Test Channel', owner=self.user)
        url = reverse('channel-detail', kwargs={'pk': channel.pk})
        data = {
            'name': 'Test Channel 2',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Channel 2')

    def test_delete_channel(self):
        channel = Channel.objects.create(name='Test Channel', owner=self.user)
        url = reverse('channel-detail', kwargs={'pk': channel.pk})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_join_channel(self):
        # Success join
        channel = Channel.objects.create(name='Test Channel', owner=self.second_user)
        channel.members.add(self.second_user)
        url = reverse('channel-join', kwargs={'pk': channel.pk})
        response = self.client.put(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(channel.members.count(), 2)
        self.assertEqual(set(Channel.objects.get().members.all()), set([self.second_user, self.user]))

        # No access to join if user in black-list
        channel = Channel.objects.create(name='Test Channel 2', owner=self.second_user)
        channel.black_list.add(self.user)
        url = reverse('channel-join', kwargs={'pk': channel.pk})
        response = self.client.put(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # No access for globally blocked user
        channel = Channel.objects.create(name='Test Channel 3', owner=self.second_user)

        self.user.is_blocked = True
        self.user.save()

        url = reverse('channel-join', kwargs={'pk': channel.pk})
        response = self.client.put(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.user.is_blocked = False
        self.user.save()

    def test_leave_channel(self):
        channel = Channel.objects.create(name='Test Channel', owner=self.second_user)
        channel.members.add(self.second_user)
        channel.members.add(self.user)
        url = reverse('channel-leave', kwargs={'pk': channel.pk})
        response = self.client.put(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(channel.members.count(), 1)
        self.assertEqual(channel.members.first(), self.second_user)

    def test_permission_required(self):
        self.client.credentials(HTTP_AUTHORIZATION='')
        url = reverse('channel-list')
        response = self.client.get(url, {'name': 'Test Channel'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ModeratorAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass1234', is_moderator=True)
        self.second_user = User.objects.create_user(username='testuser2', password='testpass1234')

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

    def test_block_globally(self):
        url = reverse('block-user', kwargs={'user_id': self.second_user.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_blocked'], True)
package example;
import wros.scene.Scene;

public final class Main {
    static final class Node {
        final Node next;
        final int[] data;
        Node(int id, Node previous) {
            next = previous;
            data = new int[(id & 3) + 1];
            data[data.length - 1] = id;
        }
    }
    private static Node retained;
    public static void main(String[] args) {
        if (args.length != 0 || Scene.abi() != 2) throw new AssertionError();
        Node head = null;
        for (int i = 0; i < 240; ++i) head = new Node(i, head);
        System.gc();
        if (head == null || head.getClass() != Node.class || head.data.length != 4) throw new AssertionError();
        retained = head;
        head = null;
        System.gc();
        int count = 0;
        for (Node node = retained; node != null; node = node.next) count += node.data[node.data.length - 1];
        retained = null;
        if (count != 28680) throw new AssertionError();
    }
}
